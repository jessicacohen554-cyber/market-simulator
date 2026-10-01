# ADDENDUM A to `PRECOMMIT-capx-d92-2026-09-10.md`

**Pushed while the four legs are solving, before any of their numbers exist.** It records the shard
launch, the validation of every artifact-grain scoring path the parent will use, and **one
DISCLOSED WEAKENING** that I cannot repair and am therefore declaring rather than discovering later.

---

## A.1 The four shards, launched at the pinned PRECOMMIT SHA

`source_revision = aac390a6f6d138203a5f6a05cd35044458cfe4ed` (full 40 characters, rule 32(c)(1) —
never a branch name). Each shard has its own `--out-dir`, its own branch, an explicit
`git add -f <its path only>`, and the named prohibitions.

| leg | arm | session | out-dir / branch |
|---|---|---|---|
| L0 | `base` (**the control**) | `session_01DLDK2rm2ourwwRmRp69VjK` | `results/ff-t3-neiso-golden/d92/base` / `claude/capx-d92-base` |
| L1 | `carbon_plus25` | `session_011iqy4SWqYQoHLgRX6Mob8V` | `…/d92/carbon_plus25` / `claude/capx-d92-carbon_plus25` |
| L2 | `gasup150` | `session_016yBcyayHjfzveN7KWXRPEC` | `…/d92/gasup150` / `claude/capx-d92-gasup150` |
| L3 | `gaspm5` | `session_015ERNQeoxNmwDanzboafJAJ` | `…/d92/gaspm5` / `claude/capx-d92-gaspm5` |

**The parent has run, and will run, no LP** (rule 32(a)). Everything below is zero-LP work on
committed artifacts.

## A.2 EVERY artifact-grain path the parent will use, VALIDATED FIRST — on the committed d46 quartet

The parent scores the paired block from SLIM artifacts (a shard never ships a multi-GB cache), so
each path is proven against the **committed `bau-d46/fc6/paired_invariants.json`** before any of my
own numbers exist. Three of four rows reproduce **byte-exactly**:

| row | path the parent will use | reproduction of the committed d46 row |
|---|---|---|
| **P1.premise** | `--paired-run-configs` (capx-D73 artifact mode) | `PASS — strictly positive delta in all 25 years (min +25.00, max +25.00 $/t)` — **exact** |
| **P3** | `--paired --pair-kind gas_pm5` over LEDGER-ONLY dirs (the committed d46 arms carry `evolution_*.json` and no parquet, so this is the real test) | `PASS — cumulative builds moved 0.0% (base 42337 MW, pert 42319 MW)` — **exact** |
| **P2** | `--paired-summaries --pair-kind gas_up` (capx-D35 artifact mode) | `PASS — year 2050: all signs correct; gas-fired 35.01→34.77 TWh, LW price 82.50→91.55 $/MWh` — **exact, plus one appended clause; see A.3** |
| **P1** | `sum(trajectory[].co2_mt)` from each arm's committed summary | base **284.42 Mt**, high **273.92 Mt** — **both operands exact against the committed detail string** |

### A.2.1 Why P1 uses the summary grain, stated as a limitation and not as a preference

`check_p1_co2_monotone` reads `_annual_co2_tons` off each arm's dispatch **parquets**, which a shard
does not ship. The summary's `trajectory[].co2_mt` is the same quantity, and the evidence that it is
the same quantity is that summing it reproduces **both** operands of the committed d46 P1 row
exactly. That is a two-point validation on the one pair where both grains exist — good evidence, and
**weaker than calling the instrument**, which is why it is written here rather than asserted later.
The parent will assemble the P1 row using the instrument's own comparison and its own detail format
(`f"cumulative CO2 base {b:.2f} Mt vs high {h:.2f} Mt"`, PASS iff `high < base`).

## A.3 THE DISCLOSED WEAKENING — P2 loses one sub-check, and it cannot be recovered

`p2_evidence_from_summary` carries **no objective value** (the summary does not record one), so the
summary-grain P2 reports `objective↑` under `not_scored` instead of scoring it:

```
committed d46 (cache grain) : "year 2050: all signs correct; gas-fired 35.01→34.77 TWh, LW price 82.50→91.55 $/MWh"
this lane   (summary grain) : "…same… [not scored at this grain: objective↑]"
```

`coal↑` is not scored on either side (NEISO holds no coal). So the parent's P2 scores **two** of the
sub-checks the committed row scored three of. The scorer's own docstring calls this out — *"never
assumed"* — and `not_scored` is explicitly "never counted as a PASS".

**Why it is not repaired.** The fix would be a fifth instruction to the shards (dump
`p2_evidence_from_run` from the cache before it is discarded). The shards were already launched, and
**this session has no channel to a running cloud shard** — `SendMessage` reaches local peers only and
the remote MCP surface here exposes `create_session` / `interrupt_session` but no `send_message`.
Interrupting four solving containers to add one line is worse than the defect. **So the P2 row this
lane emits is one sub-check weaker than the row it replaces, and the FINDING will say so on the row
itself, not in a footnote.**

## A.4 The FC-5 mechanical re-base, DRY-RUN against `d90-rescore` (the post-D77 proxy for L0)

`docs/handoffs/d92/rebase_disposition.py`, over the validated 54/54 extractor. **6 of 54 rows change
class or sign and need an authored explanation; 48 carry.** Fixed here so the authoring cannot be
mistaken for a result:

| quantity | year | model value | divergence | what is owed |
|---|---|---|---|---|
| `co2` | 2030 | 14.8849 → **6.9545** | **+60.6 % → −25.0 %** | **SIGN FLIP.** The committed text — *"Model CO2 at 2030 is HIGHER (+60 %)"* — is **falsified**. Re-author. **This is D77's named cell.** |
| `capacity:gas_cc` | 2040 | 13.1354 → **10.2006** | +2.8 % → **−20.2 %** | became divergent — needs a NEW explanation, or FC-5 reads UNEXPLAINED ⇒ **FAIL** |
| `generation:total` | 2040 | 109.2832 → **105.6935** | −12.4 % → **−15.3 %** | became divergent — same, and it clears the 15 % line by 0.3 pt, so L0's own number decides it |
| `generation:gas` | 2035 | 31.8971 → **28.4324** | +24.7 % → **+11.2 %** | became IN CORRIDOR — retire the explanation |
| `generation:gas` | 2040 | 31.9637 → **28.0428** | +28.5 % → **+12.8 %** | became IN CORRIDOR — retire the explanation |
| `capacity:fossil_peaker_steam` | 2040 | 6.7467 → **7.5887** | −18.2 % → **−8.0 %** | became IN CORRIDOR — retire the explanation |

`co2@2035` (−2.0 % → −57.0 %) and `co2@2040` (−57.4 % → −60.0 %) stay EXPLAINED DIVERGENCE and so are
classed "carry" by the mechanical pass — **but `co2@2035`'s committed text is a level-agreement
argument** (*"the −2.0 % level agreement at 2035 is where the paths cross"*) that a −57 % divergence
falsifies. **It is re-authored too**, and it is listed here, before L0 exists, so that decision is
not made after seeing a verdict. Anchors are untouched on every row (rule 13 `[R-MEASURED]`).

**These six-plus-one are the dry run, not the answer.** L0 will differ from `d90-rescore` by HEAD
drift (573 commits in the window — PRECOMMIT §3), and prediction **D9** is graded on L0's numbers,
not on these.
