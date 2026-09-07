# ADDENDUM miso-242 — D-EDGE's pre-declared `quantile_recheck` column says the **SPP hourly ladder's derive PAIRS EACH YEAR'S MISO ROWS AGAINST ALL THREE YEARS OF SPP HUB PRICES**. The confirming test **V-1…V-5 is declared here, with its bars, BEFORE it is run**

**Governs:** `PREREG-miso242-why-the-spp-seam-is-idle-2026-09-07.md` and both prior addenda.
**No bar in the PREREG moves. No decision rule changes. Q-A's, Q-B's, Q-C's, Q-D's and Q-E's
verdicts are already published** (`ADDENDUM-miso242-the-edge-decomposition-2026-09-07.md` §1) and
**nothing here can move them.** This session **does not repair** what it finds: PREREG §5.2 refused a
re-derive in advance **for every branch, this one by name**, and that refusal binds.

---

## 0. HOW THE HYPOTHESIS AROSE — disclosed against interest, and it was POST-HOC

D-EDGE was declared and pushed with a `quantile_recheck` column: the Q-Q quantile recomputed on the
**correctly paired** sample. Its output is unambiguous, and it was **not** what this session
expected:

| | committed `δ_1^import` | `quantile_recheck` import | committed `δ_1^export` | `quantile_recheck` export |
|---|---:|---:|---:|---:|
| **SPP 2023** | 14.10 | **13.4437** | −4.20 | **−2.3937** |
| **SPP 2024** | 14.49 | **17.2599** | −2.15 | **+1.4442** |
| **SPP 2025** | 21.85 | **18.5814** | +1.04 | **−2.3651** |
| **PJM 2023** | −29.17 | **−29.1702** | −93.98 | **−93.9756** |
| **PJM 2024** | −13.87 | **−13.8660** | −35.03 | **−35.0312** |
| **PJM 2025** | −15.79 | **−15.7899** | −60.49 | **−60.4944** |

PJM reproduces its committed table to the fourth decimal on all six values. SPP does not reproduce
any of its six. **The hypothesis that follows was formed AFTER seeing that column and is therefore
POST-HOC**; that is why it is not asserted here but **pre-registered as a falsifiable test with its
bars fixed below, before the test is run.**

**THE HYPOTHESIS.** `derive_spp_neighbour_hourly(g)` joins the hub series onto `g`:

```python
work = g.join(load_spp_hub_da(), how="left")      # scripts/data/derive_miso_seam_ladders.py
```

`load_joined()` returns a `(year, hour)` MultiIndex, and both the CLI (`_print_ladder(df.loc[year])`)
and the rule-23 pin test (`derive_spp_neighbour_hourly(joined.loc[year])`) pass **`df.loc[year]`**,
whose index is `hour` **alone**. `load_spp_hub_da()` is `(year, hour)`-MultiIndexed. Joining a
single-level `hour` index to a two-level `(year, hour)` index makes pandas perform a **partial join
on the shared level name**, so each of the year's 8,760 MISO rows is replicated against **all three
years'** SPP hub price for that hour index. `derive_pjm_neighbour_hourly` performs **no join at all**
(`pjm_border` is already a column of `g`), which is why PJM is unaffected — and that asymmetry is
what makes the table above a signature rather than a coincidence.

**What the hypothesis implies, and it is precise.** The 3× replication leaves every **flow**
exceedance share untouched (replicating a sample three times does not change a share), so
`P(flow > +mid_k)` and `P(flow < −mid_k)` — the estimator's **targets** — are correct. What is
contaminated is the **distribution the quantile is taken from**: a three-year mixture of the spread
instead of the year's own spread. **The targets are right; the quantile is drawn from the wrong
sample.**

## 1. V-1 … V-5, declared with their bars BEFORE the test is run

| id | what it tests | **bar** | if it FAILS |
|---|---|---|---|
| **V-1** | `g_all.loc[year].join(load_spp_hub_da())` returns exactly **3 × 8,760 = 26,280** rows, and within it `da` and the `SPP` flow column are **identical across the three year-blocks** for every hour | exact row count; max abs deviation **0.0** on both columns | the mechanism is not replication and the hypothesis is **REFUTED** |
| **V-2** | the ladder derived from that **mispaired** frame reproduces the **COMMITTED** `MISO_SEAM_LADDER_NEIGHBOUR_HOURLY_SPP_BY_YEAR` in **all 48** entries (8 import + 8 export × 3 years) | ≤ **0.005**, the pin test's own `atol`, on all 48 | the committed table did not come from this path and the hypothesis is **REFUTED** |
| **V-3** | **THE CONTROL.** PJM's derive (no join) reproduces the committed `MISO_SEAM_LADDER_NEIGHBOUR_HOURLY_BY_YEAR` in **all 48** entries on the **correctly paired** frame | ≤ **0.005** on all 48 | the reproduction failure is general, not join-specific, and the hypothesis is **REFUTED** |
| **V-4** | *REPORTED, GATED NOWHERE.* the ladder the **correctly paired** frame would produce, all 48 entries, plus the dead-band width and `Z_derive` each implies | **no bar** | n/a |
| **V-5** | whether the **POOLED** forward ladder `MISO_SEAM_LADDER_NEIGHBOUR_HOURLY_SPP_POOLED` is affected — `df.loc[a:b]` keeps the `(year, hour)` MultiIndex, so its join should be a proper two-level join | reproduces the committed pooled tuple to ≤ **0.005** on all 16 entries **from the correctly paired frame** | reported either way |

**V-1, V-2 and V-3 are jointly falsifiable and any one of them can refute the hypothesis.** V-3 is
the control that stops "the committed table doesn't reproduce" from being explained by anything
about this session's code path, hydration, or data vintage: the *same* probe, the *same* frame, the
*same* estimator, on the seam whose derive takes no join.

## 2. What this addendum does NOT do — and this is the operative half

1. **NO RE-DERIVE. NO REPAIR. NOTHING IS COMMITTED TO THE REGISTRY.** PREREG §5.2 fixed, in advance
   and for **every** branch: *"NO re-derive, NO damping factor, NO change of K, NO re-spacing of
   δ_k, NO envelope change, NO percentile change, NO interface-limit change"*, and named the
   IDENTITY-FAILS branch — **the branch that occurred** — as the one where the temptation would be
   largest. The frozen table stays exactly as committed. V-4's numbers are **REPORTED so a successor
   knows the magnitude** and are **explicitly not adopted**; they are **UN-TARGETABLE** like every
   other number in this session (PREREG §5.1).
2. **It moves no verdict.** Q-A (IDENTITY FAILS, 2023), Q-B (DISPLACED, 2025), Q-C (TABLE-INTERNAL),
   Q-D (YES) and Q-E1 (SIGN REFUTED) were published before this document and are unchanged by it.
   Note that V-1…V-3, if confirmed, **explain** Q-A's 2023 miss; they do not **cancel** it.
3. **It changes no keeper, no config, no field and no cell verdict**, and authorizes **no LP**. MISO
   stays **CALIBRATED** on `2026-09-07-miso-233-spp-hourly` with C3c as the single ledgered caveat
   and the DOF ledger at **41/2**.
4. **It does not re-open a settled adjudication** (rule 28(a)). The SPP quantity-side charter stays
   **REFUSED — NO DOF-FREE FORM** (miso-241 §5).

## 3. Stated in advance, because it will be the obvious objection

If V-1…V-3 confirm, the rule-23 pin test
(`tests/iso/miso/test_miso_seam_ladder.py::test_registry_reproduces_the_frozen_derivation`) **passed
throughout and will keep passing**, because it invokes `derive_spp_neighbour_hourly(joined.loc[year])`
— **the same call** — and therefore compares the committed table against the same mispaired output.
That is **not a failure of the test**: it pins *consistency* (the table IS the derive's output, so a
hand-edited or silently re-tuned offset fails), which is what rule 23 asks of it. It is simply not a
*correctness* pin, and nothing in this session's record suggests it was ever meant to be. **This
observation is recorded, not scored**, and it names no defect in the test.
