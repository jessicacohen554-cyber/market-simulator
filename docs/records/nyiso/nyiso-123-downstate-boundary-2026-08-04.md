# nyiso-123 — NYISO's queue is empty; the 2025 C3a failure is two objects on one boundary, and the single route to both is now an owner-chartered PAIR

**Date:** 2026-08-04 · **ISO:** NYISO · **Years:** 2023–2025 (training only, rule 22) ·
**Keeper:** `2026-08-04-nyiso-120-c119-scope`, **UNCHANGED**.

**Zero solves. Zero years touched outside 2023–2025. No `ScenarioConfig` field,
constant, derive script or artifact changed. No run produced, so none registered
(rule 15 registers runs).**

**Prereg**, committed and pushed before any measurement below:
`results/calibration/PREREG-nyiso123-downstate-boundary-2026-08-04.md`.
**Probes:** `scripts/probes/_nyiso123_month_band_allyears.py`,
`_nyiso123_zonal_identity_allyears.py`.
**Records:** `results/calibration/_nyiso123_month_band_allyears.json`,
`_nyiso123_zonal_identity_allyears.json`.
**Charter produced:** `docs/handoffs/nyiso-downstate-topology-split-charter-2026-08.md`.

**Verified at this session's HEAD, committed artifacts only, no solve:**
`scripts/calibration_verdict.py --run-id 2026-08-04-nyiso-120-c119-scope` returns
**NOT-YET** — `price_mean` **FAIL** (2023 +7.2 % PASS, 2024 −0.9 % PASS,
**2025 −10.1 % FAIL** against ±10 %), `price_tail` **CAVEAT** (ledgered, budget
**1 of 3, unspent**), the other seven **PASS**. `scripts/audit_keepers.py --iso NYISO`
**PASS, 0 failures / 0 warnings**. NYISO holds a `complete` (validation-tier) marker,
is **absent from `final`**, and the **holdout spend freeze is ACTIVE** and outranks
the marker — nothing out-of-training was solved, scored or read.

---

## §0 — the verdict in one table

| # | question | measured result | verdict |
|---|---|---|---|
| **Q1** | does nyiso-122's Jan+Feb / Jun+Jul seasonal split hold in 2023 and 2024? | **No.** 2024's winter miss is in **December** (−1.130 of −1.690, $100–300 band) and its Jan+Feb is **+1.053**; 2023's is **February** (−0.734), not January (−0.076) | the object is a **cold-snap** object, not a calendar window |
| **Q2** | did the model's defect get *worse* in 2025? | **No — it improved.** The conditional per-hour miss in the $100–300 band fell **−104.95 → −63.37 → −40.45 $/MWh**; that band's **load share rose 1.42 % → 2.75 → 14.65 %** | same defect, **10× the exposure** |
| **Q3** | is the mainland-identity share ~100 % in all three years? | **95.88 % (2024) vs 95.94 % (2025) — identical to 0.06 pp**; 2023 is **86.40 %**, materially lower | **CONFIRMS** the removed-mask reading on the pair that matters, with 2023 reported against it |
| **Q4** | did a large actual zonal spread occur in a *passing* year? | **Yes** — Feb 2023 ran a **$43.67** all-5 spread, within $0.61 of Jan 2025's $44.28, in a year that PASSED C3a at +7.2 % | the locational miss **predates 2025** |
| **Q5** | what would reproducing the observed basis deliver? | **an exact identity**: the counterfactual error **equals the load-weighted upstate gap** — **+2.45 % (2025)**, **+8.60 % (2024)**, **+24.74 % (2023)** | the split is **right for 2025** and **breaks both passing years alone** |
| **Q6** | so does §3 strengthen or weaken the topology-split case? | **BOTH, and they must be stated separately** | **STRENGTHENED** as the object; **WEAKENED** as a standalone promotion |

**Consequence, and the owner's ruling.** The `Capital_Hudson` → Zone-F/Zone-G
topology split is confirmed as the correct object for **both** halves of the
C3a-2025 failure *and* for C3c — and is confirmed to be **un-promotable alone**,
because closing the basis would expose an upstate over-pricing error that turns
2023 from PASS into a clear FAIL. Put to the owner with these numbers, the ruling
was **charter both, paired**: the split is chartered re-scoped to C3c + the winter
level miss, with a pre-registered gate that it promotes **only jointly** with the
upstate object. The charter is `docs/handoffs/nyiso-downstate-topology-split-charter-2026-08.md`.

---

## §1 — measurement bases, named up front

Three load-weighted bases for the same year appear below and are **never blended**:

| year | scorer bench `rt_lw` (the official C3a) | hub hourly actual | per-zone monthly actual |
|---|--:|--:|--:|
| 2023 | 32.30 | 32.05 | 32.04 |
| 2024 | 38.20 | 38.14 | 37.83 |
| 2025 | 66.53 | 66.37 | 64.94 |

The model side is identical on all three (34.64 / 37.85 / 59.84) and **reproduces
the scorer byte-for-byte**. Band work (§2) uses the **hub hourly**; zonal work (§3)
must use the **per-zone monthly**, because that is the only grain at which
committed per-zone actuals exist. Where a headline number is quoted, the **lift in
$/MWh is basis-independent** and is given alongside the percentage on both bases.

**One correction to the prior record, stated because it changes a month
attribution.** nyiso-122's probes mapped hour → month with a per-year
`date_range(f"{year}-01-01", …)`. The repo's canonical clock is a **fixed non-leap
8760 calendar keyed to 2023**, shared by every model year with Feb 29 dropped
(`build_ercot_as_withholding._CALENDAR`, `build_caiso_hsl`, `pipeline/ttc.py`).
The two agree exactly for the non-leap 2023 and 2025 — so **every nyiso-122 number
stands** — and differ by one day from Mar 1 onward for leap-2024. This session
uses the canonical clock for all three years.

## §2 — the month × band decomposition, extended to 2023 and 2024

`_nyiso123_month_band_allyears.py`, on the keeper's committed `hourly/` sidecars
and the committed hourly actual. **2025 reproduces nyiso-122's §1 table exactly**
(Jan+Feb −3.579 of which −3.602 is the $100–300 band; Jun+Jul −3.756 of which
−3.813 is the >$300 tail with 33 of 42 tail hours; all other months +0.803), which
is the check that the extension is measuring the same thing.

**Contribution to each year's annual load-weighted gap, $/MWh:**

| | | ≤$100 | $100–300 | >$300 | **total** | tail h |
|---|---|--:|--:|--:|--:|--:|
| **2023** | Jan+Feb | +0.862 | −0.809 | −0.199 | **−0.146** | 2 |
| | Jun+Jul | +0.749 | −0.078 | −0.039 | **+0.633** | 1 |
| | all other | +3.107 | −0.607 | −0.400 | **+2.100** | 7 |
| **2024** | Jan+Feb | +0.993 | +0.061 | 0.000 | **+1.053** | 0 |
| | Jun+Jul | +0.695 | −0.390 | −0.583 | **−0.279** | 7 |
| | all other | +0.674 | −1.411 | −0.328 | **−1.065** | 5 |
| **2025** | Jan+Feb | +0.204 | −3.602 | −0.181 | **−3.579** | 5 |
| | Jun+Jul | +0.722 | −0.664 | −3.813 | **−3.756** | 33 |
| | all other | +2.670 | −1.660 | −0.207 | **+0.803** | 4 |

### §2.1 — the Jan+Feb window is a 2025 artifact, and that matters for rule 17

The probe reports **all twelve months** and applies nyiso-122's grouping only as a
view, precisely so a year whose miss sits elsewhere says so. It does:

- **2024's worst month is December, at −1.690**, of which **−1.130** is the
  $100–300 band — the same signature as Jan+Feb 2025. Its Jan+Feb is **+1.053**.
- **2023's winter miss is February (−0.383, band −0.734)**; January is **+0.237**.

So the winter object is real in all three years and **is not a Jan+Feb calendar
window** — it tracks the cold snap, which moved. **Any future mechanism that
proposes a winter window must therefore declare a driver-derived cold-snap window,
not a month range** (rule 17 `[R-FLOOR-WINDOW]`: a floor binding outside its
driver's evidence is a bug by definition). This is recorded now because a
month-range window would have looked defensible from nyiso-122's 2025-only table.

### §2.2 — the defect did not get worse; the market's exposure to it grew 10×

Each band's contribution factors into **what the model gets wrong per hour** and
**how often the market puts it there**. Separating them changes the story:

| band | conditional per-hour miss ($/MWh) | | | load share (%) | | |
|---|--:|--:|--:|--:|--:|--:|
| | 2023 | 2024 | 2025 | 2023 | 2024 | 2025 |
| ≤$100 | +4.79 | +2.43 | +4.25 | 98.42 | 97.06 | 84.58 |
| $100–300 | **−104.95** | **−63.37** | **−40.45** | **1.42** | **2.75** | **14.65** |
| >$300 | −404.61 | −463.84 | −546.43 | 0.16 | 0.20 | 0.77 |

**The model's per-hour miss in the $100–300 band improved monotonically, by 61 %.**
What grew is the band's share of load — **10.3×**. The tail is the same shape: its
conditional miss grew 1.35× while its share grew 4.8×.

On C3a's own percentage basis (pp of that year's actual mean), the year-over-year
attribution is unambiguous:

| band | 2023 | 2024 | 2025 | **23→24** | **24→25** |
|---|--:|--:|--:|--:|--:|
| ≤$100 | +14.72 | +6.19 | +5.42 | **−8.53** | −0.77 |
| $100–300 | −4.66 | −4.56 | −8.93 | +0.10 | **−4.37** |
| >$300 | −1.99 | −2.39 | −6.33 | −0.40 | **−3.94** |
| **TOTAL** | **+8.07** | **−0.76** | **−9.84** | **−8.83** | **−9.08** |

- **2023 → 2024 is the mask removal**, essentially in full: **−8.53** of the
  **−8.83** pp swing is the ≤$100 credit collapsing.
- **2024 → 2025 is exposure growth**: **−8.31** of the **−9.08** pp swing is the
  two upper bands, whose *conditional* miss was flat-to-improving. The credit moved
  only **−0.77**.

**This sharpens nyiso-122's accounting and is reported as a correction because it
changes which mechanism the story names.** nyiso-122 attributed 2025's failure to
the removed mask, quoting the $0–25 band (39.1 % of load and +3.41 in 2023 → 7.2 %
and +0.92 in 2025). That band did move as stated, but the other trough bands
absorbed most of it, so the **credit total** fell only +14.72 → +5.42 pp and **was
already spent by 2024**. Both accounts reach the same conclusion — *2025 has no new
defect* — and the corrected one supports it more strongly, because the per-hour
defect measurably **improved** every year. The mask is real; it just is not what
2025 lost.

## §3 — the zonal identity, all twelve months, and the counterfactual

`_nyiso123_zonal_identity_allyears.py`.

### §3.1 — the identity share, and the honest answer to the brief's question

The brief expected **~100 % in all three years**. Measured, whole-year, share of
hours in which the four mainland zones price identically (<$0.01 apart):

| year | mainland-4 | all-5 | mainland-4 mean spread | C3a |
|---|--:|--:|--:|--:|
| 2023 | **86.40 %** | 71.4 % | $0.66 | +7.2 % PASS |
| 2024 | **95.88 %** | 74.6 % | $1.34 | −0.9 % PASS |
| 2025 | **95.94 %** | 80.2 % | $0.00 | **−10.1 % FAIL** |

**2024 and 2025 are identical to 0.06 pp** — that is the leave-one-year-out
comparison that carries the argument, and it **confirms** the removed-mask reading:
the model's locational blindness is unchanged between a passing year and a failing
one, so 2025 cannot be failing because that blindness appeared.

**Reported against the brief's expectation: 2023 is not ~100 %, it is 86.40 %.**
The model carried materially more zonal dispersion in 2023 than in either later
year. This is stated rather than rounded up to a clean three-year constant; it
means the "constant in all three years" form of the claim is **not** supported, and
only the 2024↔2025 form is.

### §3.2 — a passing year already ran the same actual spread

Actual all-5 monthly zonal spread and NYC−Upstate basis, the months where either
is large:

| | month | actual all-5 spread | actual NYC−Upstate | model NYC−Upstate | C3a that year |
|---|---|--:|--:|--:|---|
| 2023 | Feb | **$43.67** | $21.79 | $1.42 | **PASS** +7.2 % |
| 2024 | Jan | $22.88 | $22.88 | $2.96 | **PASS** −0.9 % |
| 2024 | Dec | $18.13 | $13.56 | $0.09 | **PASS** |
| 2025 | Jan | **$44.28** | $44.28 | $1.09 | **FAIL** −10.1 % |
| 2025 | Feb | $27.09 | $24.64 | $0.13 | **FAIL** |

**Feb 2023 ran a $43.67 spread — within $0.61 of Jan 2025's $44.28 — in a year that
PASSED.** The locational miss is a standing representation gap, not a 2025 event.
(The model's non-zero NYC−Upstate figures under a 100 %-identity month are not a
contradiction: these are *demand-weighted monthly* means, and NYC's load is more
peak-concentrated than upstate's, so identical hourly prices still yield a small
positive monthly basis.)

### §3.3 — the counterfactual, and the identity it collapses to

Anchor the model at its own **upstate** price and add the **observed** basis:
`m*[z,k] = m[Upstate_West,k] + (a[z,k] − a[Upstate_West,k])`, monthly grain,
load-weighted on the model's own demand. **Diagnostic bound only — the observed
basis is a measured outcome and under rule 13 `[R-MEASURED]` never enters a solve;
no mechanism is proposed that would consume it.**

| year | baseline C3a | **counterfactual C3a** | lift $/MWh | on the scorer's bench basis |
|---|--:|--:|--:|--:|
| 2023 | +8.10 % | **+24.74 %** | +5.33 | 39.97 vs 32.30 → **+23.7 % FAIL** |
| 2024 | +0.07 % | **+8.60 %** | +3.23 | 41.08 vs 38.20 → **+7.5 %** (in band, near edge) |
| 2025 | −7.86 % | **+2.45 %** | +6.70 | 66.54 vs 66.53 → **+0.0 % PASS** |

Substituting `m*` into the load-weighted mean, every `a[z,k]` term cancels and the
counterfactual error collapses **exactly** to one quantity (asserted in the probe,
not merely observed):

> **counterfactual error ≡ the model's load-weighted `Upstate_West` pricing error**
> — **+$1.59 (2025)**, **+$3.25 (2024)**, **+$7.93 (2023)**.

A model that reproduced the observed downstate basis perfectly would score
**exactly the C3a error of its own unconstrained upstate price**. That makes the
upstate gap — not the basis — the **cap** on what any locational mechanism can
deliver in each year, and it is the single most decision-relevant number this
session produces.

## §4 — §3(c) answered plainly: strengthened AND weakened, and they are different claims

The prereg committed in advance to reporting whichever criterion fired. Four did,
and two of them cut against the successor hypothesis:

| criterion | fired? | consequence |
|---|---|---|
| **P1** identity share equal across years | **partly** — 2024 ≡ 2025 (0.06 pp), 2023 lower | **CONFIRMS** on the pair that matters; the three-year-constant form is **not** supported |
| **P2** large actual spread in a passing year | **YES** — Feb 2023, $43.67 | **STRENGTHENS**: the boundary is a standing gap |
| **P3′** upstate over-priced in passing years, offsetting downstate | **YES** — +$7.93 / +$3.25 / +$1.59 | **STRENGTHENS the mask reading and NAMES the mask** as a distinct second object |
| **P4** counterfactual moves 2025 toward PASS | **YES** — −7.86 % → +2.45 % | the split **is** the C3a-2025 route |
| **P4′** counterfactual does not help | **YES, for 2023 and 2024** — +24.74 % / +8.60 % | the split **alone breaks both passing years** |

**Strengthened, as the object.** In 2025 the model's unconstrained marginal energy
cost is nearly right (+$1.59, +2.45 %) and essentially **all** of the C3a-2025
failure is the missing downstate basis. Both halves of that failure — the
cold-snap $100–300 miss and the summer >$300 tail — sit downstate of the same
unrepresented boundary, and Feb 2023 shows the boundary was already there while the
model was passing for an unrelated reason.

**Weakened, as a standalone promotion.** The same identity says a split that closed
the basis and changed nothing else would carry the upstate error into the score:
2023 goes **PASS +8.10 % → FAIL +24.74 %**, 2024 goes **PASS +0.07 % → +8.60 %**,
inside the ±10 % band but near its edge. That is precisely the leave-one-year-out
failure rule 22 exists to catch — in-sample gain with held-out degradation — and it
would have been invisible from 2025 alone.

**The mask now has a name.** nyiso-122 identified it as trough over-pricing. §3.3
locates it exactly: it is **over-pricing of the unconstrained upstate zone**, worth
+$7.93/MWh in 2023 and +$3.25 in 2024, which lives in the trough band because that
is where upstate-marginal hours are. It is a **second, separate object**, and it is
the one that must move with the split rather than after it.

## §5 — what is NOT claimed

1. **No mechanism was tested, proposed or armed.** No matrix cell verdict changes;
   the §5.5 status block records the new evidence and the queue stays empty of
   *levers* (the chartered pair is not a lever-queue entry).
2. **Item 4 is untouched** and remains **unadjudicated**, per the owner's ruling —
   its standalone rule 14 `[R-ACCURATE]` case still survives untested by solve. §3
   independently reinforces nyiso-122's reach refusal: NYC carries the winter gap
   and item 4 cannot move NYC in any of the 36 months.
3. **No claim the benchmark is wrong.** Every measured price here is a validation
   target.
4. **The counterfactual is not a proposal.** It consumes a measured outcome and is
   admissible only as a diagnostic (rule 13). A real split must produce the basis
   from a *constraint*, not from the observed answer — that is the charter's §3 gate.
5. **The counterfactual is an upper bound on the lift, not a neutral estimate.** It
   holds the upstate price fixed and adds basis on top; a real binding constraint
   would also depress the export-constrained upstate zone somewhat, so the true
   lift is smaller. This makes the 2023/2024 breakage a *conservative* warning
   rather than an overstated one, and it is stated because the direction matters.
6. **2023's 86.40 % identity share is unexplained.** Why the model carried more
   zonal dispersion in 2023 than 2024–2025 is not diagnosed here. It is not
   load-bearing for any conclusion above, and it is logged as an open question.
7. **The hook artifact recurred and was caught.** `.claude/hooks/ruff-autofix.sh`
   runs `ruff format .` whole-tree, and reformatted
   `scripts/data/derive_chp_power_only_heat_rates.py` — another lane's file, the
   same one nyiso-122 §5(5) flagged. It was found in the pre-commit status scan and
   restored **byte-identical to HEAD** before any commit. The hygiene note stands:
   after any edit, diff the staged list against what you actually touched.

## §6 — governance

Rule 12: no solve. Rule 13 `[R-MEASURED]`: every measured price, spread and basis is
a **validation target**; the §3.3 counterfactual is explicitly a diagnostic bound and
nothing entered a solve. Rule 15 `[R-DASHBOARD]`: **no run was produced, so none is
registered** — the keeper is unchanged and its dashboard entry is untouched. Rule 16:
n/a. Rule 19 `[R-ONE-MECH]`: the peak half remains nyiso-110's object and **no second
mechanism is proposed for it**; the charter names one object per phenomenon and pairs
them rather than stacking. Rule 21: DOF ledger unchanged. Rule 22 `[R-HOLDOUT]`:
**training years only** — both probes hard-filter to {2023, 2024, 2025} and raise
otherwise, which matters because the committed actual parquet carries 2018–2022 and
2026; the **holdout spend freeze is ACTIVE and untouched**; NYISO's `complete`/`final`
markers are unchanged and nothing was spent. Rule 23 `[R-FROZEN-DERIVE]`: nothing
re-derived. Rule 24 `[R-REGISTRY]`: no tunable added. Rule 25 `[R-ISO-SCOPE]`:
**NYISO only**. Rule 27 `[R-PUSH]`: every file authored here is new; nothing ≥300
lines was rewritten; all pushes were exact local bytes over `git push` on a
freshly-rebased base. Rule 28: duty (a) the queue was read first and found **EMPTY**,
and the off-queue element — that this session tests no mechanism at all — was declared
in the prereg; duty (b) no cell verdict changes because no mechanism was tested; the
§5.5 status block is updated in this session with the new evidence and the chartered
pair.
