# FINDING — nyiso-122: NYISO's 2025 C3a failure is TWO seasonally-separable objects, and the winter half is LOCATIONAL, not fuel. Queue item 4 is refused ex ante on measurement.

**Date:** 2026-08-04 · **ISO:** NYISO · **Years:** 2023–2025 (training only, rule 22) ·
**Keeper:** `2026-08-04-nyiso-120-c119-scope`, **UNCHANGED**, determination **NOT-YET**,
C3c (`price_tail`) the sole ledgered caveat (budget **1 of 3, unspent**).

**Zero solves. Zero years touched outside 2023–2025. No `ScenarioConfig` value,
constant, derive script or artifact changed.**

**Prereg (committed and pushed BEFORE any measurement that follows §1):**
`results/calibration/PREREG-nyiso122-iroquois-winter-spread-2026-08-04.md`.
**Probes:** `scripts/probes/_nyiso122_c3a_2025_decomp.py`,
`_nyiso122_iroquois_construction.py`, `_nyiso122_winter_zonal_spread.py`.
**Records:** `_nyiso122_c3a_2025_decomp.json`, `_nyiso122_iroquois_construction.json`,
`_nyiso122_winter_zonal_spread.json`.

> **Session renumbered nyiso-121 → nyiso-122.** The brief opened this session as
> nyiso-121; that label was already spent on `origin/main` by the MISO-matrix-column
> session, which had itself renumbered off nyiso-120 for the same reason.

---

## §0 — the verdict in one table

| # | question | measured result | verdict |
|---|---|---|---|
| **Q1** | is the 2025 C3a miss one defect or several? | Jan+Feb **−3.58** in the $100–300 band; Jun+Jul **−3.76** in the **>$300 tail**; all other months **+0.81** | **TWO objects**, seasonally separable |
| **Q2** | is the summer half the same object as C3c? | −3.81 of the −3.76 Jun+Jul gap is **above $300**; 33 of the year's 42 tail hours are in those two months | **YES — C3c.** Not touched (rule 19) |
| **Q3** | is the winter half a FUEL-LEVEL miss? | the model prices its four mainland zones **identically in 100.0 %** of Jan+Feb 2025 hours; the actual all-5 zonal spread was **$44.28** (Jan) / **$27.09** (Feb) | **NO — it is LOCATIONAL** |
| **Q4** | can `nyiso_iroquois_winter_spread` (queue item 4) reach it? | it leaves NYC delivered gas **unchanged in all 36 months** (\|Δ\| < 0.005) and NYC carries **49 %** of the winter gap; it **cuts** Upstate-January gas by **$7.48/MMBtu**, the one zone that is right | **NO — REFUSED ex ante, no solve** |
| **Q5** | would re-grounding the Tier-3 TTC estimates on measured limits help? | NYISO's own as-enforced limits: UPNY-CONED and SPR/DUN-SOUTH bind >95 % in **0.0 %** of 2025 hours, at medians **looser** than the model's estimates | **NO — my own hypothesis, refuted** |
| **Q6** | what is left? | the actual NYC−Upstate premium (**$44.28**) exceeds any plausible fuel-spread × heat-rate (**$12.75–17.00**) by 2.6–3.5×, with **no interface flow-limited** | a **sub-zonal in-city** object |

**Consequence: both halves of the C3a-2025 failure resolve to the SAME
unrepresented object — the downstate locational boundary.** The
`Capital_Hudson` → Zone-F/Zone-G topology split was chartered against **C3c alone**;
it now carries a **second, independent and larger** motivation.

---

## §1 — PHASE 0: the 2025 gap is not spread across the year

`_nyiso122_c3a_2025_decomp.py`, reading only the keeper's committed `hourly/`
sidecars (rule 15) and the committed hourly actual. **The model side reproduces the
scorer byte-for-byte** — 34.64 / 37.85 / 59.84 against the payload's own
load-weighted aggregation. (The actual side reads 66.37 vs the bench's `rt_lw`
66.53 because the committed hourly parquet has 8,758 of 8,760 rows for 2025; a
0.24 % basis difference that changes no share and no conclusion, and it is stated
rather than smoothed.)

**Month × actual-price-band contribution to the annual −$6.53/MWh gap:**

| | ≤$100 | $100–300 | >$300 | total | tail h |
|---|--:|--:|--:|--:|--:|
| **Jan+Feb** | +0.20 | **−3.60** | −0.18 | **−3.58** | 5 |
| **Jun+Jul** | +0.72 | −0.66 | **−3.81** | **−3.76** | **33** |
| all other months | +2.67 | −1.66 | −0.21 | **+0.81** | 4 |
| **year** | **+3.60** | **−5.93** | **−4.20** | **−6.53** | 42 |

Two counterfactuals bound the halves (diagnostic only — no measured outcome enters
any solve, rule 13): if the model matched the actual **exactly in every >$300 hour**
and changed nowhere else, C3a-2025 would read **−3.51 %** and PASS; if it matched
**every non-tail hour** instead, it would read **−6.33 %** and still FAIL. **Neither
half is sufficient alone and neither is negligible.**

### §1.1 — why 2023 and 2024 pass and 2025 does not

The compression is present in **all three years**, not new in 2025: the model
over-prices the trough and under-prices the peak throughout (p90/p10 model **2.697**
vs actual **4.430** in 2025 — 61 %, consistent with nyiso-109's measured 69/49/45 %
of the trough→peak swing). What changes is that **the compensating error
disappears**. The model's trough over-pricing offset its peak miss while prices were
low — the $0–25 band was **39.1 %** of load in 2023 and contributed **+3.41** — but
in 2025 that band is only **7.2 %** of load and contributes **+0.92**. 2025 does not
have a new defect; it has the same defect **with the mask removed**.

**Rule 19 `[R-ONE-MECH]` check, which the brief required before anything is
proposed: the peak-half object IS nyiso-110's.** Independently confirmed from the
committed `reserve_family` sidecars: the model's cross-family reserve price is
**$0.00 in 99.7 % of 2025 hours** (non-zero in 29 of 8,760), including **1,037 of
the 1,041** hours the market cleared $100–200. That is exactly the missing
everyday reserve-price formation nyiso-110 diagnosed and route-exhausted
(`diurnal_price_amplitude` NYISO = **G**). **No second mechanism is proposed for it.**

## §2 — the winter half is LOCATIONAL, and that is what refuses item 4

The pre-registration proposed to test the winter half with `nyiso_iroquois_winter_spread`,
a monthly gas-basis reallocation. **`_nyiso122_winter_zonal_spread.py` was run before
the solve, and it kills the arm.**

**2025 Jan+Feb, per zone:**

| zone | load % | Jan model | Jan actual | Feb model | Feb actual | contribution |
|---|--:|--:|--:|--:|--:|--:|
| Upstate_West | 34.2 | 89.82 | 90.17 | 77.52 | 87.14 | **−0.297** |
| Capital_Hudson | 13.9 | 89.82 | **127.03** | 77.52 | 114.23 | −0.946 |
| Lower_Hudson | 5.6 | 89.82 | 119.23 | 77.52 | 100.12 | −0.267 |
| **NYC** | **33.0** | 89.82 | **134.45** | 77.52 | 111.78 | **−2.164** |
| Long_Island | 13.2 | 91.69 | 130.84 | 78.83 | 111.55 | −0.776 |
| | | | | | | **−4.450** |

*(This table's basis is the committed per-zone monthly actuals load-weighted; §1's
band table uses the hub hourly actual. The two bases differ by ~0.87 $/MWh on the
Jan+Feb total — the hub is the simple mean of eleven NYISO internal zones, the model
system price is load-weighted over five model zones. **The shares, not the absolute,
carry the argument**, and both bases are named rather than blended.)*

**The model's four mainland zones price IDENTICALLY in 100.0 % of Jan+Feb 2025
hours** (mainland-4 spread mean **0.00**, median **0.00**). The market's all-5
monthly zonal spread over the same period was **$44.28** and **$27.09**.

**The model has the marginal energy cost approximately right and the location
entirely wrong**: Upstate_West January is nearly exact (**−0.35**), while NYC is
short **$44.63**, Capital_Hudson **$37.21** and Long_Island **$39.15**.

### §2.1 — the four measured reasons item 4 cannot be the lever

`_nyiso122_iroquois_construction.py` builds the fuel object **twice at one HEAD**
(no LP, no dual — the nyiso-118/119 pattern):

1. **It cannot touch 49 % of the target.** NYC's delivered gas is **unchanged in all
   36 months**, \|Δ\| **< 0.005 $/MMBtu** — because NYC's ratio is `transco_m/iroq_m`,
   so the city resolves to its own measured Transco Z6 NY monthly under **both** arms.
   NYC carries **−2.164 of the −4.450** winter gap.
2. **It would degrade the one zone that is right.** Upstate_West's January gas falls
   **−$7.48/MMBtu**, and Upstate-January is currently accurate to **−0.35 $/MWh**.
3. **It over-shoots December.** The eastern trio's largest single monthly lift of the
   year is **December +$3.67/MMBtu** — on a month the model already prices to
   **−0.06 $/MWh** (97.10 vs 98.12). *This was pre-registered in advance* (prereg
   §4.2) as an expected cost; it is now a reason not to arm, because the benefit it
   was to be traded against does not exist.
4. **Even a perfect fuel treatment is too small.** The measured NYC−Upstate gas
   spread is **$1.70/MMBtu**, worth **$12.75–17.00/MWh** at heat rates 7.5–10.0,
   against an actual premium of **$44.28**. Fuel can explain at most **29–38 %** of
   January's premium; the model currently reproduces **$0.00** of it.

**Its construction gates PASS** — annual conservation Δ = **0.00000** in all three
years, NYC untouched, blast radius the eastern trio + Upstate_West only. **The
refusal is on REACH, not on construction**, and that distinction matters for §5.

**Rule 1 `[R-STRUCT]` is the governing reason.** Arming item 4 against C3a-2025 would
raise eastern fuel costs to compensate for an unrepresented locational constraint —
reaching a better number through a mechanism that is not the real one. That is the
failure mode rule 1 names explicitly, and it is refused on that ground rather than
on the residual.

## §3 — REPORTED AGAINST INTEREST: my own successor hypothesis is refuted too

Having attributed the winter half to congestion, the obvious next lever is a rule 14
`[R-ACCURATE]` re-grounding: the model's interface TTCs are flagged **"Tier 3
(calibration) — verify against NYISO operating-limit postings"**, i.e. estimates.
NYISO's own as-enforced hourly limits **are on disk** for 2023–2025
(`data/raw/NYISO/interface-flows/`, carrying `positive_limit_mw` per interface-hour),
so the lever is **not data-blocked**. **It is refuted by that same data** (2025,
training year only):

| interface (model link) | model TTC | measured limit p50 | binds >95 %, all year | binds >95 %, Jan+Feb |
|---|--:|--:|--:|--:|
| CENTRAL EAST (Upstate_West→Capital_Hudson) | 2850 | 2900 | 3.6 % | **17.8 %** |
| UPNY CONED (Capital_Hudson→Lower_Hudson) | 5150 | **6385** | **0.0 %** | **0.0 %** |
| SPR/DUN-SOUTH (Lower_Hudson→NYC) | 3900 | **4600** | **0.0 %** | **0.0 %** |
| TOTAL EAST | — | 7550 | 0.0 % | 0.0 % |

**The model's estimates are already TIGHTER than the measured limits on both
downstate interfaces, and the real interfaces never bound at all.** Re-grounding
them on the measured postings would **loosen** them and remove what little
congestion the model has — the opposite of the needed direction. The hypothesis is
recorded as refuted rather than dropped quietly, and **the measured limits are NOT
adopted**, because rule 14's named misalignment clause applies: a single reduced
link standing for several parallel paths cannot take a literal per-interface rating.

## §4 — what the residual actually is

The market ran a **$44.28/MWh** NYC-over-Upstate premium in January 2025 **with no
interface flow-limited** and with fuel able to explain at most **$17**. That
premium is therefore **sub-zonal in-city price formation** — NYISO's local
reliability commitment inside Zone J — which is:

- the object **nyiso-97 closed on identification** (the as-enforced AORR is
  MyNYISO-walled; the public 2008-vintage Appendix B carries no derivable NYC
  parameter), and
- the target of C3c's standing re-open condition, the **`Capital_Hudson` →
  Zone-F/Zone-G topology split under its own owner charter — never a
  mechanism-flag lever**.

**The new fact this session contributes** is that the split is no longer motivated
by the summer scarcity tail alone. It now also owns the **winter level miss**, which
is the **larger** of the two halves in the months it occupies and is **not** a
scarcity phenomenon at all. Any charter written for it should be scoped to both.

## §5 — what is NOT claimed, and the one question left open

1. **This does not close item 4 as a mechanism.** What is refused is item 4 **as the
   C3a-2025 winter lever**, on reach. Its standalone rule 14 `[R-ACCURATE]` case —
   that distributing the measured annual Iroquois−Transco spread **flat** across
   months mis-states the winter physics of a Connecticut trading point inside the
   New England complex — **survives this session untested by solve** and is
   preserved as an **owner question**, deliberately not adjudicated `R`. Arming it
   would be a measured-input improvement that **degrades** C3a-2025; under rule 22
   D-5(b) that is an escalation, not a session decision.
2. **No claim that the benchmark is wrong.** Every measured price here is a
   validation target (rule 13).
3. **No claim about the >$300 tail's cause.** C3c's diagnosis and exhausted queue
   are untouched; this session neither reopens nor re-litigates them, and **no new
   ledger slot is spent** (budget stays 1 of 3).
4. **The two aggregation bases in §1 and §2 are named, not blended** (§2's note).
5. **A stray reformat of another lane's derive script was caught and reverted
   before it was committed — recorded because a silent one would be the
   nyiso-120 §6(2) error class.** The repo's own `.claude/hooks/ruff-autofix.sh`
   PostToolUse hook runs `ruff format .` **whole-tree** after every edit, so it
   line-wrapped one signature in `scripts/data/derive_chp_power_only_heat_rates.py`
   (pre-existing formatting drift on main, semantically null, and **not this
   session's file**). The hook re-stages only the file the session actually
   edited; a blanket `git add -A` swept the rest in anyway. It was found in the
   pre-commit status scan, unstaged, and restored **byte-identical to HEAD**
   before any commit. **Hygiene note for later sessions in any lane: after a
   `git add -A`, check the staged list against what you actually edited — the
   autofix hook's whole-tree scope means unrelated files can appear.**
6. **I departed from my own pre-registration, and that is reported here rather than
   in a footnote.** The prereg committed to solving a two-arm A/B. The zonal
   attribution that kills the arm was measured **after** the prereg was committed
   and pushed, and I stopped instead of spending the solve. The prereg's §4.5
   declared the C3a-2025 net direction **undetermined in advance**; that declaration
   stands and is **not** retro-fitted into a prediction of this outcome. An ex-ante
   refusal on measurement is the nyiso-93/94/95/97 discipline, and — per rule 15 —
   **no run was produced, so none is registered**.

## §6 — governance

Rule 12: no solve ran. Rule 13 `[R-MEASURED]`: every measured price and flow above is
a **validation target**; nothing entered a solve. Rule 15 `[R-DASHBOARD]`: no run was
produced, so there is nothing to register — the keeper is unchanged and its dashboard
entry is untouched. Rule 16: n/a (no solve). Rule 19 `[R-ONE-MECH]`: the peak-half
object is confirmed to be nyiso-110's and **no second mechanism is proposed for it**.
Rule 21: DOF ledger unchanged. Rule 22 `[R-HOLDOUT]`: **training years only** — every
probe hard-refuses any year outside {2023, 2024, 2025}, which matters because the
committed actual-LMP parquet carries 2018–2022 and 2026 and the interface-flow
directory carries 2018–2026; the holdout spend freeze is **ACTIVE and untouched**, and
NYISO's `complete`/`final` markers are unchanged. Rule 23 `[R-FROZEN-DERIVE]`: nothing
re-derived; the construction probe only *evaluates* a shipped function at two flag
settings. Rule 25 `[R-ISO-SCOPE]`: **NYISO only**; no other ISO's cell is stamped.
Rule 28: duty (a) the queue was read and item 4 selected from it, with the off-queue
element (no accompanying summer lever) stated in the prereg; duty (b) the cell is
stamped **this session** with the ex-ante result.
