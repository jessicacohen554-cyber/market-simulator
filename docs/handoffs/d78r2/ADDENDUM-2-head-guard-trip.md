# ADDENDUM 2 — capx D78-R2: the arm's HEAD guard TRIPPED, and the arm is DISCARDED and RE-SOLVED

**Written and pushed BEFORE the replacement leg is solved.**

## 1. What happened

The first arm leg ran 19:42:56 → 20:03:27 UTC and produced a complete bundle at
the declared key `bb6a60239d69508b`, solving `{2021, 2023, 2024, 2025}` with 2022
bridged. Then `run_full.sh` printed **`HEAD MOVED during arm`** — the guard's
exit-90 path. **PRECOMMIT §6 STOP 1 fired.**

## 2. What actually moved — stated at full magnitude, and it was my error

| question | answer |
|---|---|
| did `main` move during the leg? | **NO.** `git rev-list --count HEAD..origin/main` = **0** |
| what moved, then? | **my own branch**: one commit, `8f81bf9c`, made *while the arm was solving* |
| what was in it? | `docs/hindcast-reports/…-control-P-….md` and `docs/handoffs/d78r2/CORRECTION-1-….md` — **docs only** |
| did the solve code change? | **NO.** `git diff --stat 65e12b21 HEAD -- src/market_sim scripts/` is **EMPTY** across the whole window spanning BOTH legs |

So the property the guard exists to certify — *the two legs share one solve-code
state* — demonstrably holds, and the trip is a **procedural error of mine**: I
committed the control's report and CORRECTION 1 during the leg instead of holding
them until it finished. PRECOMMIT §5 says a rebase happens between legs and never
during one; the same discipline plainly applies to any commit, and I broke it.

## 3. Why the arm is re-solved anyway

There is a ready argument for grading the first arm: the guard is a sha-equality
*proxy* for a property that can be established directly and more strongly by the
empty code diff, and this lane's own genealogy contains the precedent — D78-R
graded two legs whose guard shas differed by a docs commit, on exactly that
reasoning (its §1: *"their guard shas differ only by the ADDENDUM 3 docs commit;
`git diff cbf98979 99245361 -- src/market_sim scripts/` is empty"*).

**The argument is declined.** PRECOMMIT §6 says *"any one kills the arm; none is
promoted past"*, and §6's closing line says a fired STOP is honored **however right
the diagnosis** — the D62 / D78 / D78-R precedent. A lane that reaches for a
correct-sounding reason to walk past its own fired gate has made that gate
advisory, and this lane exists because D78-R honored two gates it could have
argued away. The remedy costs **~21 minutes of LP**; the precedent costs more.

The distinction to D78-R is also real rather than convenient: its guard **did not
fire** — it pushed its addendum *between* legs, which is what the rule asks for.
Mine fired. A gate that fires and a gate that does not are not the same evidence.

## 4. The remedy

1. The first arm bundle is **DELETED**, not graded and not cited. No number from it
   appears in this lane's FINDING.
2. The arm is **re-solved from scratch** at HEAD `8f81bf9c` (cache cleared, so it
   is a genuine solve rather than a cache hit), with the HEAD guard armed and
   **no commit of any kind during the leg**.
3. Both `results/hindcast/pjm-2021-2025-realized-t1h-d78r2-*` paths are now in
   `.git/info/exclude`, so nothing pressures a mid-leg commit again; the arm's slim
   registered set is added deliberately with `git add -f` at registration.
4. The control leg is **unaffected**: its own guard held (`65e12b21`, ADDENDUM 1
   §1), it is unchanged on disk, and it is not re-solved. Its W4′ band and its
   limb (c)/(d) bars, both pre-registered in ADDENDUM 1 before any arm existed,
   stand exactly as pushed.

## 5. What this does NOT change

No gate, edge, declared class, classification rule, STOP or flip-condition limb
moves. The declared arm key `bb6a60239d69508b` is unchanged and the replacement leg
must realize it. The W4′ band `[9,394.156 , 12,518.310]` and the point value
`9,394.156` were fixed in ADDENDUM 1 **before the first arm ran** and are not
recomputed — the replacement arm is graded against the band the control already
wrote down.
