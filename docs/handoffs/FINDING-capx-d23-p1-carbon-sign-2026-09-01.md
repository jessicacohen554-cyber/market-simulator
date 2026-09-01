# FINDING — capx D23: the FC-6 P1 "carbon-sign defect" attributed — the model is right; the instrument's premise is inverted

**Session:** D23 (capacity-expansion / Forecast Finalization track), branch
`claude/capx-d23-p1-carbon-sign-0x5whn`. **Date:** 2026-09-01. **HEAD at launch:**
`6c7f82da`. **Precommit** (pushed before any measurement):
`docs/handoffs/PRECOMMIT-capx-d23-p1-carbon-sign-2026-09-01.md`. **Phase 0 held:** zero
solves; every number below is from the committed D21 arms, the base evolution ledger, and
code/constants reading at HEAD.

**Headline: neither leg is a model defect. The model's carbon-price response has the
RIGHT sign in both.** The single root cause of P1's FAIL is the arm construction: a
nonzero `ScenarioConfig.carbon_price` REPLACES the resolved carbon signal (documented,
deliberate, single-consumer semantics), and the NEISO base already carries the projected
RGGI allowance trajectory — **$26.05/t in 2026 escalating at the published 7 %/yr RGGI
CCR rate to $132.16/t by 2050**. The `carbon25` arm therefore did not raise the carbon
price; it CUT it, in every single year of the horizon (−$1.05 in 2026 widening to
−$107.16 in 2050). Cumulative CO2 rising +52.4 %, ~3 GW less CCS, and LOWER prices in
the "carbon" arm are all the model responding correctly to a large carbon-price
DECREASE. P1 measured the premise of its own pair, not the model's economics.

---

## 1. Charter discipline

No solve, no re-run, no third arm. No parameter, threshold, band, expectation, verdict,
board, keeper, shard, or marker touched — D21's FC-6 FAIL and the golden's HOLD stand
exactly as scored. No mechanism tested, no `ScenarioConfig` field added, no matrix cell
minted (duty (a) discharged: the NEISO shard's `ccs_retrofit_screen: K/K` and
`state_carbon_pricing: K` cells stand untouched; every repair routed below is
instrument-side). Backcast namespace untouched; no holdout year; no workflow. The
precommit's candidate set, kills, and adjudication order were followed as frozen; §6
scores my pre-stated expectations against the outcome, misses included.

## 2. The mechanism chain (each link verified in committed code/config)

1. **Both arms arm the RGGI program.** The resolved configs differ in exactly one
   scenario field: `carbon_price: 0.0 → 25.0` (784 flattened keys, 5 diffs, the other
   4 bookkeeping). `state_carbon_pricing=True`, `carbon_price_path="zero"`,
   `carbon_program_price_path=None`, `mass_cap_enabled=False`, `mode="forecast"` in
   BOTH (`fc6/arms/*/run_config.json`).
2. **The base's effective carbon price is the RGGI projection, not zero.**
   `policy/carbon.py::resolve_carbon_price` precedence: (i) nonzero `carbon_price`
   returned directly; (ii) else the program adder via
   `policy/cap_and_trade.py::resolve_carbon_program` — in forecast mode with the
   default `carbon_price_path="zero"`, `projected_price()` = last measured RGGI
   clearing price (NEISO anchor: $24.35, 2025, `STATE_CARBON_PRICE_BY_ISO`) escalated
   at `escalation_rate=0.07` (RGGI CCR floor-band rate). This is the EM-6 seam fix —
   "forecast carbon is no longer zero for a program ISO" (`docs/codebase/05-policy.md`).
   Projected values: 2026 $26.05 · 2028 $29.83 · 2032 $39.10 · 2035 $47.90 ·
   2040 $67.18 · 2045 $94.23 · 2050 $132.16.
3. **The override is replacement, by design, documented at the registry.**
   `config.carbon_price` has exactly ONE consumer in the model —
   `resolve_carbon_price` (policy/carbon.py:73) — and the `ScenarioConfig` field
   comments state the semantics twice: `carbon_price_path` "used when carbon_price is
   0.0"; `state_carbon_pricing` charges the program "when carbon_price is 0.0". No
   other code conditions on the field (grep-verified). So `replace(cfg,
   carbon_price=25.0)` = "disarm the RGGI trajectory, install flat $25".
4. **Every carbon consumer sees the same resolution**, so each arm is internally
   coherent: dispatch/screen mc (`runner.py:2247 → assemble_mc`, the single mc site:
   `+ emission_rate × carbon`, uniform, correct sign/units), the capacity-evolution
   driver (`runner.py:1882 → evolve_fleet` → CCS screen + new-entry screen), and the
   interchange seam (`runner.py:2399`). The arm-vs-arm comparison is "escalating RGGI
   vs flat $25" everywhere at once.
5. **The signal gap explains the trajectory gap year by year.** Signal delta
   (arm − base): −$1.05 (2026) → −$4.83 (2028) → −$14.10 (2032) → −$33.68 (2038) →
   −$42.18 (2040) → −$107.16 (2050). CO2 delta: +0.21 → +0.61 → +0.63 → +1.73 → +7.28
   → +10.05 Mt — monotone-widening with the gap. LW price delta: the "carbon" arm is
   CHEAPER in every year, −$0.40 (2026) → −$15.67 (2050) — impossible against a
   carbon-free base, and 2026's −$0.40 ≈ −$1.05/t × ~0.38 t/MWh is exactly a
   gas-CC-marginal passthrough of the signal CUT.

## 3. Leg D — the 2026 same-fleet dispatch rise: adjudication

| Candidate (precommit §3) | Verdict | Kill evidence |
|---|---|---|
| **D4 pair semantics / second armed instrument** | **CONFIRMED — the cause** | §2 chain: base 2026 signal $26.05 > arm $25; arm cheaper by $0.40/MWh; CO2 +0.21 Mt is the correct-sign response to a −$1.05/t cut |
| D1 offer/accounting emission-rate asymmetry | KILLED | one `assemble_mc` site charges `emission_rate × carbon` to every generator from the SAME `fleet.emission_rate` array the accounting reconstruction uses (`run_full_horizon._co2_tons` / checker `_annual_co2_tons`: dispatch × `context.emission_rate`); no mask/exemption branch |
| D2 sign/unit error | KILLED | `+ er × carbon` (legacy_bins.py:340), er t/MWh vs price $/t; price-delta magnitude consistent (§2.5) |
| D3 storage/renewable interaction | KILLED as cause | no carbon term in storage/renewable offers (objective: ε + dispatch adders only); D4 carries the magnitude and its year profile |
| D5 commitment/floor interaction | KILLED | golden posture arms NO P0-pattern-dependent mechanism: `commitment_enabled=False`, all three ISO bridges False, `reliability_floor=False`, `reliability_floor_overrides={}` |
| D6 import/accounting scope | KILLED | import tranches carry border carbon in VOM, never `emission_rate` (in-state CO2 total can't be inflated by imports); the border adder itself is CAISO-only (`wecc_border_carbon_adder`) |

**Leg D verdict: the model is right.** A $1.05/t cheaper carbon signal makes dispatch
slightly dirtier and power slightly cheaper. The dispatch-era response tapers exactly as
substitution saturates (semi-response ~1.2 %/$ in 2026 falling to ~0.05 %/$ by 2039 as
the 1–3 GW unabated-CC margin exhausts). A per-class 2026 decomposition is not
committable evidence (the arm has no hourly/per-class artifacts) and is not needed: the
aggregate signature (CO2 up, price down, magnitude matching marginal intensity) is
complete for attribution.

## 4. Leg C — the CCS retrofit divergence: adjudication

| Candidate (precommit §4) | Verdict | Kill evidence |
|---|---|---|
| **C5 pair semantics** (= D4) | **CONFIRMED — the cause** | as §2; the screen consumed $29.83→$132.16 in base vs flat $25 in the arm |
| C2 carbon asymmetry inside the screen | KILLED | `model/capacity_evolution/ccs.py:299–337` implements spec §5.6 verbatim-in-substance: `mc_unabated = hr·gas + vom + er·carbon`; `mc_post = … + er_residual·carbon + captured·transport`; both margins `Σ max(0, p − (mc − attr [− q45]))·avail` over the SAME prior-year price row |
| C3 realized-dispatch counterfactual | KILLED | margins are pro-forma per-MW; no realized generation anywhere in the screen |
| C4 pool/entry channel as defect | KILLED as defect | `new_entry.py:1117` charges thermal candidates `co2 × carbon_price` (and CCUS its residual, line 350). The arm's 4,000→5,000 MW unabated-CC entry cleared while paying flat $25 — rational at that price with 45Q expired; base's identical 1,000 MW CC entries (ledger 2041/2043) retrofit to CCS the following year (2042/2044) at $72–88/t — rational at THAT price. Both arms coherent under their own signals |
| C1 real-mechanism-with-surprising-sign | MOOT | there is no surprising sign to explain — see below |

**Leg C verdict: the model is right, and not even surprisingly.** Stated with the
signal correctly labeled, the screen's cross-arm response has the textbook sign — the
HIGH-carbon world (the base!) retrofits more: 15,049 MW CCS by 2050 vs 9,993.5. The
fine structure confirms the economics: through the §45Q window (2028–2032) the arms
retrofit within 55.5 MW of each other (11,539 vs 11,483.5 by 2032 — the $85/t credit
dominates a ≤$14/t signal difference); ALL divergence is post-45Q, where carbon
economics alone decide — base converts its H-class 3 GW in 2040 at $67/t and every
subsequent CC entry on arrival, while flat-$25 never clears another retrofit. D21's
reading ("the screen retrofits the entire CC fleet at carbon_price=0", "~3 GW less CCS
*because of* the carbon price", "a pure dispatch reordering under the carbon adder that
INCREASES emissions") is superseded: the base was never a carbon-zero world.

## 5. Magnitude accounting (full +110.32 Mt attributed)

- **2026–2039, fleets near-identical (≤55.5 MW CCS apart): +13.00 Mt** — dispatch
  responding correctly to a −$1 → −$38/t signal gap.
- **2040–2050, fleet divergence era: +97.32 Mt** — the retrofit/entry response to
  −$42 → −$107/t.
- Sum: **+110.32 Mt = the P1 delta exactly.** ~12 % dispatch-channel, ~88 %
  capacity-channel, both correct-sign. Nothing left unattributed.

## 6. Precommit scorecard (misses reported at full size)

- Leg D: I pre-stated DEFECT-expected with D1 (rate asymmetry) primary, D4 secondary.
  **D1 was wrong; D4 — the named secondary — is the cause, and it is an instrument
  defect, not a model defect.** My "benign unlikely (~1-in-10)" was miscalibrated
  against the actual resolution: the model behaved benignly; the pair did not.
- Leg C: pre-stated 60/40 defect-vs-real. **Outcome: neither implementation defect nor
  surprising-sign real mechanism — the 40-side "real" resolution, but with the
  surprise dissolving entirely once the premise is corrected.**
- Magnitude: "Leg C carries the large majority" held (88 %). "Leg D ≲0.3 Mt/yr
  pre-2028" missed — 2027/2028 ran +0.68/+0.61 Mt (the signal gap was already
  −$3 to −$5/t, which my precommit did not anticipate because it did not yet know the
  base carried an escalating trajectory).
- The dependency rule (Leg C possibly downstream of a Leg-D defect via the price
  signal) was moot: there is no Leg-D defect; both legs are parallel responses to one
  input difference.

## 7. Instrument blast radius (what else this premise breaks)

- **P1 pairs are premise-broken for every program ISO** — NEISO (this case), CAISO and
  NYISO (both carry programs with measured anchors and the same projection seam) —
  whenever the base leaves `carbon_price=0` with default paths. ERCOT/MISO pairs are
  clean (no program ⇒ base truly $0; a 0→25 pair there tests what it claims).
- **T1.1's own ladder** (`carbon_price ∈ {0,25,50,100}`, pre-registered ~2026-07,
  before EM-6): rung 0 IS the RGGI world for a program ISO, sitting ABOVE rung 25 in
  every NEISO year, above rung 50 from ~2036 and rung 100 from ~2046. The
  {25,50,100} sub-ladder remains internally monotone; every comparison against rung 0
  is inverted. The pre-registration was valid when written (pre-EM-6, forecast carbon
  for program ISOs WAS zero); the EM-6 seam fix silently inverted it. Chronology:
  battery plan pre-registered ~2026-07 (first NEISO run 2026-07-12, crashed, #2063);
  the unified resolver with the projection seam is in place at the golden vintage
  `9e56f0f` (2026-08-30); D21 ran 2026-08-31.
- **P2/P3 are unaffected** (`gas_price_factor` is multiplicative — no replacement
  semantics), consistent with their PASSes.
- **T1.2's cap expectation** ("carbon_price=25 clears its allowance dual at ≈$25")
  reads as the same absolute-knob mental model; whoever owns R1 below should re-check
  it against `mass_cap_enabled` interaction semantics before its first real run.

## 8. Repairs — routed, priced, admissibility-screened, NOT built

- **R1 (instrument guard; recommended first): premise assertion in the paired checker
  and the battery scorer.** Before scoring P1 (and any T1.1-style carbon ladder),
  compute `resolve_carbon_price(cfg, y)` for every solve year from each arm's
  committed config; unless the "high" arm's effective signal ≥ base's in every year,
  emit a MIS-CONSTRUCTED/vacuous row instead of a scored PASS/FAIL (the FC-6.2
  vacuous-evidence lane). ~40–80 lines + tests in `check_forecast_invariants.py` and
  the battery/scorer; no solve; strictly evidence-tightening — the exact D21
  `f0243cbf` precedent class. Rules 13/21: no measured data, no tunable — admissible.
  Instrument amendments need the director/rubric-owner sign-off D21's did.
- **R2 (re-arm recipes — a director cost decision; each ≈2×25-yr solves, ~11–30 min
  each solo per D21's timings, plus re-score):** (i) both arms
  `state_carbon_pricing=False` + `carbon_price {0,25}` — clean test of the exogenous
  channel, sacrifices program realism in base; (ii) arms at
  `carbon_program_price_path` mid-vs-high — monotone effective signal by
  construction, existing registry, but tests program-escalation response (a different
  economic question from "+$25 federal"); (iii) an additive `carbon_price_adder`
  field — the faithful "federal price on top of RGGI" object, but a new
  `ScenarioConfig` field (rule 28: matrix row + every-shard cell in the same PR) AND
  it presupposes the R4 design answer. Not this lane's call.
- **R3 (docs):** the `scenarios.py` `state_carbon_pricing` comment still reads
  "measured allowance price … a no-op everywhere else" — pre-EM-6 text that now
  misdescribes forecast behavior (the code path is projection-armed); the
  driver-battery plan needs a program-ISO note on rung semantics; D21's finding §5.2
  should gain a superseded-by-D23 cross-reference. Route to a docs/sync-docs pass —
  D21's file is not edited by this lane.
- **R4 (owner design question):** SHOULD a scenario `carbon_price` replace the program
  price (current documented semantics), floor it, or stack on it? In the real market a
  federal carbon price would coexist/interact with RGGI, not erase it — but any answer
  must remain ONE documented semantic (rules 19/24). Owner decision; nothing moved
  here.
- **FF program consequence:** `neiso-t3`'s FC-6 P1 FAIL stands AS SCORED on the
  committed arms. Whether it is re-scored under R1's guard (which would reclassify P1
  from FAIL to MIS-CONSTRUCTED-vacuous — a verdict-basis change) or re-run under an R2
  recipe is the director's call, explicitly not exercised here.

## 9. Answer to the charter's question

**Which leg is a defect, and which is the model being right in a way we did not
expect?** Neither leg is a model defect, and the capacity leg is not even the model
being right in a *surprising* way — both legs are the model being right in the
ORDINARY way about a question nobody realized was being asked: what happens when
NEISO's carbon price is cut from an escalating RGGI trajectory ($26→$132/t) to a flat
$25/t. Emissions rise, CCS retrofits fall, power gets cheaper. The defect is real but
lives one level up, in the FC-6 arm construction and pre-registered rung semantics —
an instrument premise written before the EM-6 seam fix and silently inverted by it.
P1, "the model's economic core" gate, FAILed on the instrument's own premise; the
economic core it set out to test passes the very experiment that was actually run.
