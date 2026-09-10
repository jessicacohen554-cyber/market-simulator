# ADDENDUM to PRECOMMIT-spp-64 — I MIS-COMPUTED THE G-2 PRE-SOLVE DELTA. The bar is NOT being re-cut.

**Lane** SPP-64 · **Written** before any arm number existed — see §3, which records the evidence for
that claim · **Charter** `docs/handoffs/PRECOMMIT-spp-64-stgas-selfcommit-2026-09-10.md` §5–§6.

## 1. THE ERROR

PRECOMMIT §5 computed the mechanism's footprint from the **artifact** floor —
`committed_pct × nameplate`, held over each plant's top-`online_frac` hours — and reported a 2023
forced increment of **4.894 TWh**. G-2's band **[+2.0, +7.5] TWh** was set around that number.

**That is not the floor the engine builds.** `data/fleet/arrays.py` clips each tranche to
`pmax × availability` in every hour (an outage relaxes the floor) and distributes the level
cheapest-first across the plant's tranches. Re-computed from the **engine's own `min_gen` array** on
an on-recipe `run_year(fleet_only=True)` rebuild of the 2023 arm — the same instrument PRECOMMIT §3
used, now read for the floor's *time shape* rather than only its total:

| quantity | value |
|---|---|
| ARM floor energy (`min_gen`, ST_GAS) | **3.8701 TWh** *(unchanged from §3 — this number was right)* |
| CONTROL ST_GAS dispatch (keeper's committed sidecar) | 7.0867 TWh |
| hours where the floor binds **above** control | 3,855 |
| floored hours (floor > 0) | 8,351 |
| **PRE-SOLVE LOWER BOUND on ΔST_GAS = Σₜ max(0, floorₜ − controlₜ)** | **1.3000 TWh** |

The keeper already dispatches ST_GAS above the floor in most floored hours, so the floor's *binding*
increment is **1.30 TWh, not 4.894**. §5's 4.894 answered "how much energy does the artifact floor
sit on", which is not the question G-2 asks.

## 2. WHAT I AM DOING ABOUT IT — NOTHING, AND THAT IS THE POINT

**The G-2 band stays exactly as pre-registered: [+2.0, +7.5] TWh.** A realized ΔST_GAS below +2.0
**STOPS the arm**, and if that happens the stop stands as written.

Rule 1 `[R-STRUCT]` condition (c) forbids selecting a bar by whether it makes a criterion pass.
Widening G-2 to admit 1.30 now — with a solve in flight — would be indistinguishable from that, even
though I have seen no arm number, and "I corrected my arithmetic first" is exactly what a lane
fitting a gate would also say. **The rule is worth more than this arm.** So the corrected number is
published as *evidence*, not as a new bar.

**What this means for reading the screen, stated in advance:**

- ΔST_GAS **inside [+2.0, +7.5]** → G-2 passes on its own terms and this addendum changes nothing.
- ΔST_GAS in **[+1.30, +2.0)** → G-2 **STOPS the arm**, and the stop is **on my mis-set bar, not on
  the mechanism**: the arm would in that case be behaving exactly as its corrected arithmetic says.
  The lane will report the STOP and this correction together and **put the question to the owner**,
  rather than self-authorizing a re-screen or a re-cut.
- ΔST_GAS **below +1.30** → the mechanism is under-performing its own lower bound, which is a real
  structural failure and a genuine STOP.
- ΔST_GAS **above +7.5** → over-reach, a genuine STOP.

**No other gate is touched.** G-1, G-3, G-4, G-5 and G-6 are unaffected — none of them was derived
from the 4.894 figure. G-3's ≥ 0.80 allocation bar is if anything now *better* specified: the
engine stamps the floored hours directly as `MECH_ST_GAS_MUSTRUN_PER_PLANT` in `min_gen_mechanism`,
and §1's rebuild confirms the window construction the PRECOMMIT described
(`k = round(frac × hours)`, `target[argsort(-sys_load)[:k]] = level`).

## 3. WHY THIS IS PRE-RESULT, AND HOW TO CHECK

At the moment this was written the screen shard's branch `claude/spp64-screen-2023b` carried exactly
one commit — `ffa15c8934d221b2f375831ea1db056b38f66ec4`, *"SPP-64 screen shard: heartbeat addendum
(pin + blank §6 gate table) before any LP"* — and no `docs/RESULT-spp64-screen-2023.md` existed on
any ref. The parent has run no LP at all (rule 32 `[R-SHARD]`). **The commit order in git history is
the check**: this addendum lands before the shard's result commit, and if it does not, disregard it.

## 4. THE OTHER NUMBER THIS CORRECTS

PRECOMMIT §5's per-year footprint table ranked the screen year on the same artifact-basis statistic
(2023 **4.894** > 2025 3.367 > 2024 2.803). The engine-basis lower bound is only computed for 2023
here, so **the ranking is not re-verified** and 2023 stands as the declared screen year. Two things
make that safe rather than convenient: the choice was **published before the solve**, and it was
demonstrably **not** the residual choice (2024 carries the larger C1 miss, −9.71, and the smaller
footprint on either basis). Re-deriving the other two years' engine-basis bounds costs two more
fleet rebuilds and no LP; it is left as a routed item because changing the screen year *after*
launching the screen would be a far worse practice than leaving a ranking coarsely computed.

## 5. WHAT DOES NOT CHANGE

The C1 bar (`FUELMIX_VOL_CAP_TWH = 8.0`, so **+0.38 TWh for 2023 and +1.71 TWh for 2024**), the
rule-19 enumeration, the rule-17 driver, the DOF finding (zero free parameters added), and the
G-DRIFT audit are all untouched — none of them depended on the 4.894 figure. **Note the tension this
correction creates and does not resolve**: a 1.30 TWh lower bound clears 2023's +0.38 bar
comfortably but sits *below* 2024's +1.71, so on the corrected arithmetic the 2024 row is no longer
obviously reachable by this mechanism alone. That is reported now, before the screen result, because
it is the kind of thing a lane discovers afterwards and quietly omits.
