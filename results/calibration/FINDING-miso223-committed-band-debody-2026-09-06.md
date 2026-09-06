# FINDING miso-223 — THE SCREEN **KILLS THE ARM ON G-1**. The committed-band de-lift moves the 2024 body **−$0.65** against a pre-registered **−$1.0…−$2.2**, so the band carrying 47.4 % of lifted-class ENERGY is not where the body price is set. Keeper unchanged (2026-09-06)

**KEEPER UNCHANGED → `2026-09-05-miso-220-nonsteam-lift`** (bundle
`results/calibration/miso220_nonsteamlift_B`), determination **CALIBRATED**, C3c the single
ledgered caveat. **The screen bundle is NOT registered on the dashboard and is DELETED before
this PR merges** (rule 29 clause 2 + clause (c), owner ruling R-AV): every number this session
will ever cite is in this document. Rule 22 `[R-HOLDOUT]`: 2023–2025 only; the screen solved
**2024 alone** and the remaining years were never spent.

Records: `PREREG-miso223-committed-band-debody-2026-09-06.md` (+ Addenda A–D),
`scripts/probes/_miso223_body_tail_phase0.py` → `_miso223_body_tail.json`,
`scripts/probes/_miso223_screen_gates.py` → `_miso223_screen_gates.json`.

---

## 0. Verdict in one paragraph

The session was chartered on "the miss in July 2025 and the overshoot in August for 2023 and
2024". **Phase 0 established those are one defect, not two** — a price distribution that is
too flat, whose body is too high in **36 of 36** train months (+$8.71 / +$8.24 / +$8.54 by
year) and whose tail is too low in **33 of 36** (−$15.62 / −$18.91 / −$44.17), with
corr(monthly error, actual hours > $100) = **−0.676**. A month with real scarcity reads as a
miss; a month without reads as an overshoot. **The arm — reverting miso-220's ×1.10 lift on
the `committed` band only — is DEAD on its own pre-registered gate.** It moved the 2024 body
by **−$0.653** against a declared **−$1.0…−$2.2**: the right direction, ~35 % of the
predicted magnitude, so the mechanism does not do what its own arithmetic said and G-1 stops
it. The lesson is specific and is the session's most transferable result: **`committed` carries
47.4 % of lifted-class ENERGY but sets the price far less often than that**, and energy share
is the wrong proxy for marginal frequency when the gate is a price gate. That was my footprint
metric, chosen in the PREREG, and it is the thing that was wrong — not the gate.

## 1. THE GATE TABLE, exactly as the blind scorer printed it

The scorer was committed **before either solve finished** and is unedited since.

| gate | scorer | measured | reading |
|---|---|---|---|
| **S-1** single delta | FAIL | `n_band_diffs = 11`, set exactly as declared; `other_config_diffs` = `weather_year` 2023↔2024, `gas_price_override` 2.54↔2.19, + 3 fields absent from the keeper | **ARTIFACT — substantive condition MET.** See §2 |
| **S-2** liveness | **PASS** | recorded table == declared table exactly | clean |
| **G-1** body direction & magnitude | **FAIL** | control $30.343 → arm $29.690, **Δ = −$0.653**, band [−2.2, −1.0] | **THE REAL KILL** |
| **G-2** tail confinement | **PASS** | control $51.621 → arm $50.632, Δ = −$0.989, band \|Δ\| < 3.0 | confinement holds |
| **G-3** no C1/C2 flip | FAIL | arm cells `{}`, `scored: false` | **UNSCORED, not failed.** See §2 |

**The arm dies on G-1 and on G-1 alone.** S-1 and G-3 do not contribute to the verdict and
are not claimed as kills.

## 2. THE TWO NON-KILLS, disclosed rather than scored away

**I did not edit the scorer to make either pass.** Changing a gate after seeing its result is
the move rule 1 `[R-STRUCT]` exists to forbid, and it stays forbidden when the change would be
*correct*. Both are reported at full magnitude with the scorer's own verdict intact.

**S-1 is a year-span artifact.** Its substantive condition — *exactly 11
`offer_curve_by_group` `committed` values differ and nothing else* — is **met**:
`n_band_diffs = 11` and the set is exactly the declared eleven. The failure comes from its
second clause, which compares every other `run_config` field. The keeper is a **2023–2025**
bundle whose `run_config.json` is stamped for **2023**; the arm is **2024-only**. So
`weather_year` (2023 vs 2024) and `gas_price_override` (2.54 vs 2.19) differ **because they
are year-scoped**, not because the arm changed them — and three further fields
(`cc_duct_peaking_row_scoped`, `ccs_retrofit_fixed_cost_co2_scaling`,
`unit_outage_extract_basis_share`) are simply absent from the older keeper config, the same
new-field set Addendum D classified INERT. A single-year screen against a multi-year keeper
cannot satisfy that clause as written; the clause, not the arm, is what needs fixing, and a
successor session should scope it to non-year-scoped fields **before** it runs.

**G-3 was never scored.** `replay_keeper` on a single year writes no `metrics.json`, so the
arm's C1/C2 cells are empty. The scorer **refuses to pass on empty inputs** — the miso-200
vacuous-pass trap, closed deliberately in advance — and therefore reports `pass: false` with
`scored: false`. That is the guard working, not a finding. **The named `CC_REGULAR`-2024 kill
exposure (0.053 TWh of headroom) is consequently UNTESTED**, and nothing here may be read as
having cleared it.

## 3. WHAT G-1 ACTUALLY MEASURED, and why it is worth the LP

The pre-solve arithmetic, fixed in the PREREG: miso-220's uniform ×1.10 added **+$1.86** to
the 2024 body across all four bands; reverting the band carrying **47.4 %** of lifted-class
energy should return "most but not all" of it, declared as **−$1.0…−$2.2**.

It returned **−$0.653 — about 35 %** of the lift, from a band holding 47.4 % of the energy.
Direction correct, magnitude wrong by ~2–3×.

**The inference, and it is the successor-pointing part.** Price is set by the **marginal**
tranche, not by the tranche carrying the energy. A band can hold half the fleet's output and
still sit inframarginal in most hours — which is exactly what a *committed* (stay-online) band
is built to do. The body price is therefore being set predominantly in the bands **above**
committed — `econlo`, the `econc00–05` coal ladder, and `mustrun` — and a successor arm aimed
at the body must be aimed there, with its footprint measured as **marginal frequency**, not
annual energy.

**G-2 corroborates rather than merely passing.** The tail moved −$0.989 against a −$0.653
body: the change is genuinely confined to a bid-level shift, with no structural leakage into
scarcity hours. The mechanism is real and well-behaved. It is simply small.

**This does not rehabilitate the ×1.10 lift, and nothing here is evidence for it.** Phase 0's
finding stands untouched: the lift bought C3a-2025 (−12.3 → −7.0) mostly out of the body, and
the mean passes by cancellation of a +$8 body error against a −$18…−$44 tail error. What
miso-223 establishes is only that the `committed` band is **not the lever** that unwinds it.

## 4. THE SUCCESSOR OBJECT, independent of this arm and larger than it

`data/renewables.py` puts MISO in `_UNCURTAILED_FALLBACK_ISOS` and deliberately grosses the
EIA-930 delivered wind shape up by the Potomac Economics (MISO IMM) measured annual
curtailment rate — `delivered / (1 − 0.049)` — expressly so the LP "still curtails endogenously
and responds to changed build". **The gross-up works. The LP then curtails essentially none of
it:**

| | 2023 | 2024 | 2025 |
|---|---:|---:|---:|
| EIA-930 delivered, TWh | 91.72 | 98.25 | 98.94 |
| uncurtailed potential handed to the LP | 96.45 | 103.31 | 104.04 |
| model dispatch | 96.43 | 103.31 | 104.03 |
| **LP curtailment, % of potential** | **0.001** | **0.000** | **−0.003** |
| rate the gross-up assumed | 4.90 | 4.90 | 4.90 |

Wind therefore never sits below its bound, is never marginal, and its **−$26/MWh PTC offer
never reaches the price** — which is precisely the hard floor phase 0 measured: **$17.18
minimum across 210,240 committed zone-hours**, against an actual MISO that cleared below $20
in **1,781 / 3,097 / 510** hours and went negative in 2023 and 2024 (min −$39.16).
`renewables.py` already names this quantity a standing diagnostic ("never a fit target",
CLAUDE.md #11); it currently reads **~100 % unexplained**. **No lever is proposed for it here**
and no cell verdict moves on it.

## 5. GOVERNANCE — what this session got wrong, recorded because the record is the deliverable

* **A control solve was launched that rule 29(b) never entitled it to.** §7 asserted G-DRIFT
  LIVE from a **file count** (66 files / +5,985 / −856) and two solve-adjacent filenames —
  verbatim the *"files changed, therefore void"* heuristic the rule names as **not** a reason
  to spend an LP. **The owner corrected it** ("the control is the last keeper no more
  controls"); Addendum C withdrew §7 and Addendum D then ran the audit properly. **Every hunk
  is INERT — form 4 was valid all along and no control was ever owed.** The audit took ~2
  minutes; avoiding it cost two OOM-killed control attempts and a CI detour.
* **A CI workflow was built for a memory limit that was self-inflicted.** Four solve attempts
  died at the 13 GB session cgroup because no swapfile existed.
  `FINDING-miso169-15gb-memory-fit-2026-08-19.md` §3 documents the recipe — 8 GB swapfile,
  `MARKET_SIM_HIGHS_THREADS=4` (I had set `1`, the forecast lane's value), openpyxl, the
  package pins — and with it the solve ran to `exit=0` at a ~13.2 GB peak with **698 MB** of
  swap touched. **The calibration log should have been searched for a prior memory incident
  before any infrastructure was written.** `.github/workflows/calibration-solve.yml` remains as
  usable dispatch-only tooling and carries the measured finding that a standard
  `ubuntu-latest` runner is **7 GB** — smaller than the session — but it was not the route and
  should not be treated as one.
* **The screen's own footprint metric was the wrong one** (§3): annual energy, where the gate
  is a price gate that depends on marginal frequency. Recorded so a successor does not repeat
  it.

## 6. WHAT IS NOT DONE, and is deliberately not done

The arm is **dead**; it is not re-tuned, re-scoped, or re-run at another value. Rule 29:
*"A screen that kills an arm is reported as the session's result and the remaining years are
never spent"* — 2023 and 2025 were not solved. No promotion, no dashboard registration, no
`ScenarioConfig` field minted, DOF ledger unchanged at **41/2**. Matrix (rule 28b): the
`offer_curve_by_group` MISO cell keeps **`K`** — armed in the keeper and unrefuted; what this
session refuted is one *parameterisation* of it, in the miso-215/221 "evidence about the
container" form.

**Standing items unchanged:** miso-214's result that 62–70 % of the missing CT energy was
produced below the plant's own delivered cost; `ordc_scarcity_overlay` `G` on miso-163's
structural grounds; miso-221's measurement that only 10.2 % of the supply above the clearing
price at the model's annual maximum hour carries an `offer_curve_by_group` entry; miso-222's
finding that the ELMP emergency range is 3.4–11.8× short; and every 2025 C1 cell `SKIPPED` on
a preliminary EIA-923 vintage.
