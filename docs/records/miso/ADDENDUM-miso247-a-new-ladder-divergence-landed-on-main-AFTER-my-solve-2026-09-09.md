# ADDENDUM miso-247 (fifth) — **A NEW `MISO_SEAM_LADDER_BY_YEAR` DIVERGENCE EXISTS AT MY FINAL HEAD, IT IS LARGE, AND IT IS NOT MINE.** Diagnosed and cited, **NOT** silenced and **NOT** tolerated: no tolerance is widened, no exception list is re-added, and no re-derive is made without a screen

**Governs:** nothing already published. The keeper, its determination, every gate and every band in
`FINDING-miso247-the-P19-posture-at-MISO-2026-09-09.md` are **unchanged**. This records a defect
discovered at the final rebase, after the promotion had been solved, scored and committed.

---

## 1. THE FAILURE, AT FULL MAGNITUDE

`tests/iso/miso/test_miso_seam_ladder.py::TestHourlySppOverlay::test_registry_reproduces_the_frozen_derivation`
**FAILS** at my final head. 2023 SPP import offsets, registry against a live re-derive:

```
ACTUAL  (committed registry): [ 13.44,  30.30,  50.82,  83.92, 123.33, 152.94, 152.94, 152.94]
DESIRED (re-derived at HEAD): [ 10.62,  25.73,  43.07,  62.47,  83.98,  90.56,  90.56,  90.56]
        8 / 8 elements mismatched · max absolute difference 62.38 · max relative 0.689
```

**This is not the one-cent class miso-244/245 closed.** It is a 69 % relative move on every band of
the seam.

## 2. **IT IS NOT MINE, AND THE PROOF IS STRUCTURAL RATHER THAN ASSERTED**

**`git diff origin/main...HEAD -- src/ data/raw/ scripts/lib/ scripts/data/` is EMPTY.** This session
changed **no solve-path code and no source data** — only docs, probes, dashboard payloads and the
keeper/matrix stamps. A registry-vs-derive divergence cannot be produced by that diff.

**THE CAUSE, CITED.** `86e45462` (2026-09-09, *"Repair the SPP actual-LMP clock: the sidecar was on
SPP's GMT market interval, the model is on fixed CST"*) rewrote
**`actual_lmp_hourly_SPP.parquet`** — **the exact series MISO's SPP hourly ladder is Q-Q derived
against**. Shifting that series' clock moves every quantile, which is precisely the observed
signature.

**THE TIMELINE, WHICH IS FAVOURABLE TO ME AND IS THEREFORE STATED PRECISELY RATHER THAN LEANED ON:**

| | contains `86e45462`? |
|---|---|
| `b849a51b` — session-start HEAD, where `D-5` was measured | **NO** |
| `f29b7ab0` — the basis my full span actually solved on (`run_config.git.basis_sha`) | **NO** |
| `79b19877` — the main I rebased onto at the FINAL push | **YES** |

**So the keeper's solve did not consume the repaired SPP series, and `G-DRIFT`'s `D-5` was valid for
the tree the solve ran on.** The divergence became visible only at the last rebase. **It affects the
`miso-245` predecessor identically** — both keepers carry the same frozen table — so it is not a
cost of this promotion, and it would not have been avoided by declining it.

## 3. **WHAT IS *NOT* DONE, and each is the thing the standing rule forbids**

The handoff's standing instruction is verbatim: *"NEVER widen that tolerance and NEVER re-add an
exception list — a new divergence is a source-data change to diagnose and cite, not a tolerance."*

* **The `atol=0.005` bar is NOT widened.**
* **`_MISO244_KNOWN_LADDER_DIVERGENCES` is NOT re-added.** It was DELETED, not zeroed, at miso-245
  under rule 26 `[R-DELETE]`, and a deleted exception list stays deleted.
* **The test is NOT skipped, xfailed, or silenced in any way.** It fails, and it should.
* **NO RE-DERIVE IS MADE HERE.** Rule 23 `[R-FROZEN-DERIVE]` licenses one — the source data
  genuinely changed and the commit is cited — but re-deriving the SPP bands changes the LP's own
  inputs, so it is a **new structural object** owing rule 29 `[R-SCREEN]` a phase 0, a screen year
  named on its own footprint, and a full span. **Doing it unscreened, in the same session that
  already promoted a different object, is exactly the discipline this lane exists to keep.**

## 4. THE OTHER FAILING TEST IS ANOTHER LANE'S (rule 25 `[R-ISO-SCOPE]`)

`tests/scoring/test_gate_a_provenance.py::test_live_board_passes` fails on **SPP**:
`gate.a_keeper_marker` cites the superseded `2026-09-07-spp-3-screened-input` against SPP's live
`2026-09-09-spp-51c-oversupply-curtailment`. **MISO's row passes** — `check_gate_a_provenance.py`
reported OK on the 7-row board after this session re-keyed MISO. Re-keying SPP's row is **SPP's
lane's R-T duty**, and rule 25 forbids this lane from touching it.

## 5. HANDED FORWARD — the successor's first item, ranked

**The SPP-ladder re-derive is now MISO's most concrete open object**, ahead of the coal deficit,
because it has a **cited cause** (`86e45462`), a **licensed route** (rule 23), and a **failing pin**
holding it visible. Its charter: re-derive `MISO_SEAM_LADDER_BY_YEAR`'s SPP entries on the repaired
clock, citing the data change and **never a residual**; screen it on its own footprint; carry the
whole 192-entry pin at `atol=0.005` with **no exceptions**.

## 6. Non-claims

1. **Nothing published is revised.** The keeper, its CALIBRATED determination, `G-1`'s failure and
   every band stand exactly as published.
2. **No tolerance widened, no exception list re-added, no test silenced.**
3. **The favourable timeline is evidence about causation only** — it does not make the divergence
   less real or less this lane's to fix.
4. **No re-derive, no screen and no second promotion** was attempted in this session.
