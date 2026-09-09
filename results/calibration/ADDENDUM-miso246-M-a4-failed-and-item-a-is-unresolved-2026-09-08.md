# ADDENDUM miso-246 (second) — **`M-a4` FAILED IN 2023, SO ITEM (a) IS `UNRESOLVED` ON MY OWN PRE-REGISTERED RULE.** No bar is moved, no repair is made — the leg was SATISFIABLE and two of three years cleared it. Published first, at full magnitude. **A GAP IN MY OWN §3 CLASSIFICATION RULE is disclosed**, and one REPORTED-ONLY characterisation is declared here, with NO decision rule, before it is computed

**Governs:** `ADDENDUM-miso246-my-own-gate-G-PARSE-failed-because-main-moved-under-it-2026-09-08.md`
§4 `M-a4` and, through it, the classification of PREREG item **(a)**. **`G-PARSE′`, `G-MODE`,
`G-ISO`, `G-BASIS`, `G-BUS`, `G-RECON`, §3a's bar, `M-a1`, `M-a2`, `M-b1`, `M-b2` and `M-c1` are
UNTOUCHED.** Machine record: `results/calibration/_miso246_lever_queue_census_phase0.json`,
provenance-stamped at HEAD **`c4ba68a1`**, tree clean.

---

## 0. **`G-PARSE′` PASSES — stated once, and it is not the news**

All three limbs hold: **L1** all seven shards recover **313** cells; **L2** strict == loose in every
shard; **L3** the artifact now carries HEAD, the dirty flag and the blob sha of every parsed file.
**No literal was widened**; the `312` is deleted. This adds no evidence for anything — it only
removes the way the first run could be wrong.

## 1. **THE FAILURE, AT FULL MAGNITUDE**

```
FAILED_LEGS: ['M-a4: 2023: eq_share 0.9993, |dsigma| 1.0027']
```

| year | limb (i) share \|`p_bus` − `p_MISO-Indiana`\| ≤ $0.01 (bar ≥ **0.99**) | limb (ii) \|σ(`p_bus`) − σ(`p_Indiana`)\| (bar ≤ **$0.05**) | |
|---|---:|---:|---|
| **2023** | 0.9993 **PASS** | σ **6.0942** vs **7.0969** ⇒ **$1.0027** | **FAIL** |
| 2024 | 0.9999 **PASS** | 16.5253 vs 16.5410 ⇒ **$0.0157** | **PASS** |
| 2025 | 1.0000 **PASS** | 15.2118 vs 15.2118 ⇒ **$0.0000** | **PASS** |

**`M-a4` REQUIRED BOTH LIMBS IN EVERY YEAR. IT FAILED. ON THE RULE I FIXED BEFORE THE NUMBER
EXISTED — *"If EITHER limb fails at ANY year, item (a) is reported UNRESOLVED, no reclassification is
made"* — ITEM (a) IS `UNRESOLVED`.**

**NO BAR IS MOVED AND NO REPAIR IS MADE, and the reason matters:** `M-a4` was **satisfiable** —
2024 and 2025 clear both limbs, 2025 to the bit. This is a **result**, not a broken gate, and the
`G-PARSE′` treatment (delete the literal, repair stricter) has **no analogue here**. Re-scoping
`M-a4` to 2024–2025, excluding hours, or relaxing the σ bar to $1.05 would each convert a failure
into a pass by construction. **None is done.**

**WHAT THE FAILURE COSTS ME, SAID PLAINLY.** `M-a4` was the leg that would have let item (a) be
classified `G` — refused as an already-scored object (C3b / C3c) rather than left open. Without it,
**item (a) is not disposed of**, and the census carries it as open. That is the direction that costs
the "queue empty" reading, and it is the direction the rule points.

### 1a. WHAT IS ESTABLISHED ANYWAY, AND IT IS NOT NOTHING

The failure is **year-specific and one-limbed**. Limb (i) — the identity itself — **PASSES in all
three years**, at 0.9993 / 0.9999 / **1.0000**. Read with `M-a2`'s pre-registered decomposition
(ladder-exclusive **0.0007 / 0.0001 / 0.0000** against zone-exclusive **0.8478 / 0.8492 / 0.8758**),
what is measured is that **`p_bus` is the model's own internal Midwest price to the cent in
essentially every hour, and the seam ladder explains essentially none of it exclusively.** What is
**not** established is that the two series are the same *distribution* — in 2023 they are not, by
**$1.00 of σ**, and that gap is the whole failure.

**A FACT AGAINST A PUBLISHED CLAIM, reported as measured.** miso-174 recorded the keeper's Midwest as
*"a perfect copper plate (zonal price spread exactly 0.00 in all 8,760 h of all three years)"*. On
**this** keeper the max cross-zone spread over the five Midwest zones is **$0.746786 in 2023** and
**exactly $0.000000 in 2024 and 2025**. The keeper differs (miso-174 predates seven promotions), so
this is not a contradiction of that session — but the claim does **not** hold verbatim at HEAD, and
2023 is the same year `M-a4` fails in.

## 2. **A GAP IN MY OWN §3 CLASSIFICATION RULE, DISCLOSED RATHER THAN PAPERED OVER**

PREREG §3 gives six ordered classes — `A`, `G`, `D`, `B`, `S`, `LIVE` — and defines `LIVE` as *"a
backcast-lane MISO route with a **DOF-free form**, an admissible measured series, and no standing
refusal."* **An OPEN ATTRIBUTION QUESTION WITH NO CANDIDATE MECHANISM NAMED FITS NONE OF THEM.** It
is not `A` (never adjudicated), not `G` (no rule refuses it), not `D` (class `D` asks whether every
*form* carries a free parameter, and there is no form to ask about), not `B` or `S` (the data exist),
and not `LIVE` (LIVE requires a form). **My rule has no slot for it, and I did not notice when I
wrote it.**

**The consequence, stated so a reader can apply their own reading rather than mine:**

> The FINDING will report such routes in a distinct class **`Q` — OPEN ATTRIBUTION, NO CANDIDATE
> MECHANISM**, disclosed as a class the pre-registered rule did not provide. **On the PREREG's own
> verdict rule a `Q` route is NOT `LIVE` and therefore does NOT make the queue non-empty** — that is
> what the rule as written says, and it is not re-written here. **A reader who holds that an
> unadjudicated open question belongs in the queue should read the verdict with `|Q|` added, and the
> FINDING will state `|LIVE|` and `|Q|` separately and give both readings, so the choice is the
> reader's and not mine.**

## 3. **DECLARED HERE, BEFORE IT IS COMPUTED: ONE REPORTED-ONLY CHARACTERISATION, WITH NO DECISION RULE**

I intend to characterise **why** 2023's σ gap exists. It is declared before it is computed so it
cannot be shaped to a conclusion, and it carries **NO decision rule of any kind**:

> **`P-a5` (REPORTED ONLY).** For 2023, the hour set `H≠` = {t : \|`p_bus`(t) − `p_Indiana`(t)\| >
> $0.01}: its size; the mean and max of `p_Indiana` and `p_bus` on it; where those hours sit in the
> year's own `p_Indiana` distribution (their price decile membership); and the σ of `p_bus` and
> `p_Indiana` with `H≠` removed.

**THE ARITHMETIC SHOWING IT MOVES NOTHING, fixed here in advance.** `M-a4`'s limb (ii) is defined on
the **full-year** σ, which is the statistic that failed; the last item above (σ with `H≠` removed) is
**exactly the excluded-hours computation §1 refuses to make the bar**, and it is computed only to
*describe* the failure. **Item (a) is `UNRESOLVED` whatever `P-a5` returns**, `M-a4` is not re-run,
no bar moves, and no route changes class on the strength of it.

## 4. **A CONSEQUENCE FOR ITEM (b), RECORDED AND NOT USED TO MOVE ITS VERDICT**

`M-b2` returned **MERIT 3–0** on its own pre-registered rule (`Γ_merit` +0.1791 / +0.1866 / +0.3559
against `Γ_ceiling` **−0.1290 / −0.1912** / +0.1254). That verdict **stands and is not re-opened**:
Manitoba's determinism deficit is carried by the **merit-set** hours, i.e. by whatever sets `p_bus`.

**But item (a) has now failed to identify what that is**, so **item (b) inherits item (a)'s
`UNRESOLVED` status** rather than being closed by it. `M-b2` answered its own question and handed the
result to a leg that did not answer its own. **That is a worse outcome for this session than the one
I expected, and it is the one the rules produce.**

## 5. Non-claims

1. **`M-a4`'s failure is not withdrawn, re-scoped or repaired**, and its per-year values are fixed
   above before anything else is written.
2. **No bar is moved anywhere in this session** — `G-PARSE′` deleted a stale literal in favour of
   literal-free identities; nothing else changed.
3. **`P-a5` can promote, refuse and close nothing**, and item (a) is `UNRESOLVED` independently of it.
4. **Class `Q` is a disclosure, not a new rule.** The PREREG's verdict rule is applied exactly as
   written, and both readings are given so the reader chooses.
5. **Zero LP**; DOF **41/2**; no `ScenarioConfig` field created or changed; keeper unchanged.
6. **No out-of-training year is solved, scored or registered, and no marker is sought or implied.**
7. **MISO has no failing gate**, this session does not invent one, and **C3c is untouched.**
