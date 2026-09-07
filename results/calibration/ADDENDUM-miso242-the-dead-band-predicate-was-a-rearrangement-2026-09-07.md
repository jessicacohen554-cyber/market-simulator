# ADDENDUM miso-242 — **THIS SESSION'S OWN G-DB GATE FAILED.** The PREREG's F3 stated the dead band as an ALGEBRAIC REARRANGEMENT of the merit test, and the two are not the same predicate in IEEE arithmetic. The repair is declared here, **before the repaired numbers exist**

**Governs:** `PREREG-miso242-why-the-spp-seam-is-idle-2026-09-07.md` §0 F3, §1 leg **G-DB**, and the
dead-band share used by **Q-A**, **Q-B** and **Q-D**. Pushed **before** any repaired quantity is
computed. **No bar is moved. The repair makes the gate STRICTER.**

---

## 1. THE FAILURE, PUBLISHED FIRST AND AT FULL MAGNITUDE

The probe pushed with the PREREG ran. **Five of six provenance legs pass exactly**; the sixth —
**G-DB, this session's own falsifiable identity leg — FAILED**:

| leg | result |
|---|---|
| **G-T** | PASS — committed SPP + PJM tuples equal the PREREG's F2 quotation; **0** monotonicity violations |
| **G-Z** | PASS — SPP zero-flow share **0.4175 / 0.4066 / 0.4810**, `env_i`=0 **0.0106 / 0.0035 / 0.0034**; |Δ| = **0.0000** on all six |
| **G-L** | PASS — `ceiling_active_share` **0.2572 / 0.2952 / 0.2474**, mean import bands in merit **0.5035 / 0.4880 / 0.3311**; |Δ| = **0.0000** on all six |
| **G-ID** | PASS — **0.0 MW**, **0** prefix violations, 12 seam-leg-variant cells × 3 years |
| **G-B** | PASS — repaired harness `corr` **0.9917 / 0.9935 / 0.9935** (|Δ| 0.0000), level **8.9 / 1.8 / 5.8 MW** (|Δ| 0.02 / 0.05 / 0.03) |
| **G-DB** | **FAIL — 16 / 1 / 26 disagreeing hours on SPP** (bar: **0**). PJM: **0 / 0 / 0** in every year. |

**43 hours in total across three years, all on SPP, all in the same direction** (the band-count
route says zero-flow, the rearranged-inequality route says not).

## 2. THE CAUSE, DIAGNOSED FROM THE OPERANDS — it is a defect in the PREREG's own F3, not in the instrument

Every one of the 43 hours is an **EXACT TIE**: `p_bus(t) − (spp_hub(t) + δ_1^export) == 0.0` to the
bit. Six representative 2023 hours: `p_bus` 46.168698 / 57.000500 / 50.674401 / 42.411801 /
38.720399 / 36.178799 against `spp_hub` 50.368698 / 61.200500 / 54.874401 / 46.611801 / 42.920399 /
40.378799, `δ_1^export` = −4.20 — difference **0.000e+00** in each.

`build_recons` does not use one operand form; it uses **two**, and the PREREG did not notice:

```
import leg   mi = (sig_i > d_i)          with sig_i = p_bus − anchor      → a SPREAD (subtraction)
export leg   me = (p_bus < anchor + d_e)                                  → a LEVEL  (addition)
```

The PREREG's F3 wrote the dead band as `δ_1^exp ≤ (p_bus − anchor) ≤ δ_1^imp` — the export edge
**rearranged into the spread form**. In exact real arithmetic the two are identical; in IEEE double
arithmetic they are not, because `fl(p_bus − anchor)` may round strictly below `δ` in exactly the
hours where `fl(anchor + δ) == p_bus`. That is precisely what the 43 hours are: `p_bus < anchor + δ`
is **False** (band out of merit ⇒ zero flow, which is what the model does) while
`(p_bus − anchor) ≥ δ` is also **False** (the rearranged band says "not in the dead band"). PJM's
`δ_1^export` is −93.98 / −35.03 / −60.49, far from any realized `p_bus − border`, so **no tie can
occur there — which is why PJM reads 0/0/0 and is corroboration, not luck.**

**This is a defect in this session's own pre-registered statement of the identity.** The instrument
is not wrong; the PREREG's rearrangement of it was. It is disclosed here before anything is
recomputed.

**Reported, never gated, and it is not noise:** an exact tie at `p_bus = spp_hub + δ_1^export` is the
signature of the **SPP export band 1 being exactly marginal at the external bus** — the LP dual
equals the marginal offer. 16 / 1 / 26 such hours is a fact about the keeper's dispatch and is
recorded as one; **no verdict is attached to it and no bar reads it.**

## 3. THE REPAIR — declared here, BEFORE the repaired numbers exist, and it is STRICTER

**Every dead-band membership test in this session — G-DB, Q-A, Q-B and Q-D alike — is recomputed in
the instrument's OWN two operand forms**, never in a rearrangement of them. For a price series `x`
and an anchor `a`:

```
in dead band (x, a)  :=  (x − a  ≤  δ_1^import)   AND   (x  ≥  a + δ_1^export)
                          ^ the import leg's own subtraction   ^ the export leg's own addition
```

applied with `x = p_bus` for the MODEL basis (`Z_model`) and `x = MISO hub DA` for the DERIVE basis
(`Z_derive`, `Z_derive^K`), against the same frozen committed `δ`.

**Why this is stricter, not looser.** The bar is unchanged at **zero disagreeing hours** and **no
tolerance is introduced anywhere**. What changes is that G-DB now tests the F3 identity against the
predicate the code actually evaluates, instead of against an algebraically-equivalent rearrangement
of it — so a genuine defect in the merit predicate (a flipped sign, a non-monotone ladder, a wrong
anchor) still fails it, while a bit-level rearrangement artifact no longer can. A gate that could
only be passed by *loosening* it would be the opposite move, and is not made.

**No bar moves.** `TOL_SHARE` 0.002, `TOL_MEAN_N` 0.01, `TOL_ID_MW` 1e-6, `TOL_CORR` 0.002,
`TOL_LEVEL_MW` 0.5, **`QA_BAR` 0.020 and `QB_BAR` 0.050** are all exactly as pushed with the PREREG.
The PREREG's §4 decision table, §5 freezes and §6 non-claims are untouched and bind unchanged.

## 4. THE BOUND ON WHAT THE REPAIR CAN DO — fixed HERE, before the repaired numbers exist

The repair can only reclassify hours that are **exact ties**, and G-DB has counted them: **16 / 1 /
26** of **8,741 / 8,760 / 8,712** `ok` hours. So **every** dead-band share this session reports can
move by at most

```
0.0018  /  0.0001  /  0.0030      (2023 / 2024 / 2025)
```

and every one of those movements is in the **same** direction (a tie hour joins the dead band).
That worst case, **0.0030**, is **6.7× below Q-A's 0.020 bar** and **16.7× below Q-B's 0.050 bar**.

**Therefore, stated before the numbers: the repair CANNOT flip Q-A's verdict, Q-B's verdict, Q-C's
decision-table row, Q-D's gated comparison or Q-E's sign leg, under any arrangement of the 43
hours.** If a verdict were to change, that would itself be evidence of a further defect and would be
published as one. `Z_derive` and `Z_target` in Q-A are unaffected in a second way as well: `Z_target`
is a function of measured flow alone and contains no price comparison at all.

## 5. What this addendum does NOT do

1. It does **not** move a bar, add a tolerance, or change any decision rule, decision table, freeze
   or non-claim in the PREREG.
2. It does **not** change the instrument. `build_recons`, `identity_check` and `classify_leg` are
   still imported unmodified from miso-241; G-B still pins this session to the **repaired** export
   pricing and passed at |Δcorr| = 0.0000.
3. It does **not** touch the committed ladder, the envelope, its percentile, or any interface limit
   (rules 14 / 23). **No re-derive.** The read-only derive verification the probe already carries is
   reported and gated nowhere.
4. It charters nothing, arms nothing, solves nothing, and moves no cell verdict.
5. Every number in §1 and §4 is **UN-TARGETABLE**, exactly as PREREG §5.1 fixed.
