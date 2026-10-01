# FINDING miso-180 — the anchored SPREAD-ONLY graft is real, clean, and INERT: the LP realizes +0.13 pp of the predicted +0.59, Δ₁ does not move, the South dipole stands — the across-unit dispersion family closes with the residual relocated OFF the offer stack

**Session:** miso-180 (2026-08-23). **Keeper `2026-08-22-miso-177-rho-measured`
UNCHANGED.** Verdict **`I` (INERT)** by the pre-registered §6 mapping — all
kills silent, G-2 measured inert. **Both runs REGISTERED**
(`2026-08-23-miso-180-control` / `2026-08-23-miso-180-anchored`, full 3-year
bundles with hourly sidecars incl. `reserve_family`, rule 15/16). **PREREG:**
`PREREG-miso180-anchored-spread-2026-08-23.md`, committed and pushed at
`14ea321` BEFORE the anchor identification or any new hour-set-conditioned
quantity existed; the probe + Phase A record landed at `daa339b`, the
implementation + matrix row at `111ef27`, the A/B scorer at `e9c3c2e` — in
the prereg's own order.

**Charter:** the owner granted FINDING-miso179 §3's named successor as
**D-1b** in the session prompt — the anchored SPREAD-ONLY object chartered in
kind, the corpus refetch authorized only if the anchor identification needed
book statistics beyond the committed artifact (it did — §1). D-2 (the 5(i)
seam-response ruling) and D-3 (the South under-export evidence) were NOT
granted and were not touched; both now carry sharper evidence (§5).

**The one-paragraph answer.** The one open design question — the anchor rank
— was adjudicated ex ante in writing (candidate (i), the model/book H\*
crossing rank, an inputs-only path; (ii) book-knee and (iii) conduct-boundary
rejected; anti-sweep clause honoured: computed once, no variant tried). The
anchor landed at **r = 0.875** with textbook geometry (a SINGLE crossing,
model $56.55 vs eligible book $55.54 at the anchor, zero under-gridpoints
below it). Every Phase A kill cleared (K-a 0.387 vs ≥ 0.5; K-b 2023 predicted
+1.77 % vs ±10; K-c 2025 predicted +0.592 pp vs ≥ +0.5 — narrowly). The
mechanism was built gated, proven inert off (G-0 control bit-identity 12/12
at HEAD), and armed as a single delta. **It behaved exactly as designed and
moved almost nothing:** realized ΔC3a-2025 = **+0.132 pp** (−11.747 →
−11.615; the G-2 inertness line is ±0.25), realized 2023 = +0.061 pp,
2024 = +0.000 pp. The body was untouched to three decimals (+1.451 →
+1.452 pp), the movement lived entirely in the tail (+0.03) and top decile
(+0.09) — perfect shape discipline — but **Δ₁ stayed at +10.45 of a $5.28
gap** (was +10.50) and **MISO-South's over-price did not move toward zero**
(+16.96 → +17.15 %). The static predictor's declared no-substitution
overstatement measured **4.5×**: when the top 12.5 % of the affected stack
gets more expensive, the LP clears imports and mid-stack committed supply
instead. The across-unit dispersion family is now fully adjudicated
(level form `R`, spread form `I`) and the 2025 residual is precisely NOT an
offer-level object: it is **what the model dispatches instead of ever
reaching the top of its stack** — the mid-stack supply surplus at the
binding hours (imports +2.1 GW, gas −5.3 GW; miso-178 §5), which is exactly
the open D-2 seam-response question.

---

## 1. What was done (all committed / reproducible)

* **Anchor identification needed the corpus:** the committed
  `_miso179_dispersion_precheck.json` carries only 5-point H\* book
  summaries; the crossing rule needs the 199-grid curves. Refetch executed
  under the charter's conditional grant: 552/552 zips fetched, DA curated —
  and the substrate BYTE-VERIFIED to be miso-179's (curated DA row counts
  equal the derive record exactly: 10,890,729 / 10,871,544 / 11,187,592;
  every committed miso-179 H\* statistic — model 5-point, book-ALL, book
  ELIG, both K-PRE-b masses — reproduces to its committed rounding).
  DISCLOSED PREREG AMENDMENT, executed at the gate's intent level: the
  prereg's manifest-sha leg is unsatisfiable by construction
  (`manifest.json` embeds `fetched_utc`, so the whole-file digest can never
  reproduce across fetches — discovered at intake, before the probe ran);
  the content-level checks above are strictly stronger for what the anchor
  consumes. Both digests recorded in the probe JSON.
* **The anchor** (probe `_miso180_anchored_spread_precheck.py` →
  `_miso180_anchored_spread_precheck.json`): r = 0.875 by the frozen rule
  `max{p ∈ GRID : Q_mod_H*(p) ≥ Q_book_elig_H*(p)}`; sign changes 1; guards
  (0.50, 0.975] clear. Both 199-point curves are committed in the record —
  the fine-grain identification miso-179 lacked.
* **Phase A:** K-a CLEAR at **0.387** (mean above-anchor rise model $32.92
  vs eligible book $85.00 — the tail-scoped object is ~2.6× the model's own,
  unlike the p90−p10 ratio 0.541 that killed the level form); K-b CLEAR
  (anchored static predictor: C3a-2023 +1.28 → +1.77 %, 10 exposed hours,
  all August); K-c CLEAR narrowly (predicted 2025 shift **+0.592 pp** vs
  the +0.5 stop; 59 exposed hours, mean raise $26.61, max $151.58; July
  carries +0.54 pp of it).
* **The mechanism** (`miso_offer_spread_anchored`, default off, MISO-gated;
  `data.offer_curves.apply_miso_offer_spread_anchored` on the BASE cost at
  the seam after the offer-margin family, in both the backcast and forecast
  orchestrators): per calendar month, pmax-weighted midpoint ranks of the
  affected econ/peak tranches' month-mean `mc_base`; tranches above the
  anchor floored raise-only at `A_m + (Q̂(r) − Q̂(a)) × G_ref(m)`. Params =
  the committed miso-179 vector (sha pinned in constants) + the identified
  anchor (cited constant). Cache-key drop-at-default (68 pin tests pass;
  armed key distinct); 7 unit tests (raise-only, rank preservation, scope
  exclusion, sha pin, zero-affected hard-error, off + non-MISO inertness);
  matrix base row + all six shard cells in the same commit as the field
  (rule 26(c)).
* **The A/B** (miso-169 15 GB recipe: pinned stack incl. python 3.11 +
  pydantic 2.13.4 per the bundle's recorded environment,
  `MARKET_SIM_HIGHS_THREADS=4`, 8 GB swapfile; solves ALONE, years
  sequential): control `miso180_anch_A`, arm `miso180_anch_B`
  (`replay_keeper --set`, single delta). Graft telemetry: 1,534/1,538/1,536
  affected tranches, ~3,000 tranche-months raised per year, max graft
  target $478.97/$465.57/$444.34 — under the $500 maxgen ceiling in every
  year (ceiling encounters unchanged control→arm: 0/6/0 hours ≥ $500).

## 2. The gate record (`_miso180_ab_gates.json`)

| gate | result |
|---|---|
| G-0 control bit-identity | **PASS 12/12** — every scored sidecar of every year max\|diff\| = 0 vs the committed keeper (HEAD drift-free; default proven inert at solve grain) |
| G-1 arm validity | PASS — flags recorded (arm true / control false), artifact sha = pinned `b4e72312…`, anchor consumed = 0.875 = identified, telemetry > 0 all years |
| G-2 C3a-2025 direction | **INERT** — Δ = **+0.132 pp** (−11.7466 → −11.6146; band ±0.25) |
| G-3 against-interest band | PASS — arm 2023 **+1.339 %**, 2024 **−4.056 %** (both inside ±10) |
| G-4 C3b | PASS all three years |
| G-5 conduct | PASS — C8 gated classes all PASS on the arm, ZERO new D-4 failures vs the regenerated control |
| G-6 DOF | PASS — `n_residual` unchanged at 2; the two new ledger entries are `measured` (vector + anchor), zero fitted scalars |
| G-7 record flips | PASS — zero PASS → non-PASS flips arm vs the committed keeper |

Determinations: keeper NOT-YET, control NOT-YET, **arm NOT-YET on C3a
(price_mean) alone** — same posture as the keeper, C6 attested (the arm's
attestation generated from the keeper's per the gen_miso169 pattern:
`scripts/gen_miso180_attestation.py`).

## 3. The measurements the verdict rests on (all in the two committed records)

**Static-predictor audit** (the declared overstatement, now measured):

| pp shift | 2023 | 2024 | 2025 |
|---|---:|---:|---:|
| predicted (no substitution) | +0.49 | +0.05 | **+0.59** |
| realized (LP) | +0.06 | +0.00 | **+0.13** |

**Bucket decomposition, 2025 (arm vs control, pp of C3a):** the 88-hour
actual RT>$200 tail −9.614 → −9.587 (+0.027; model tail mean $66.24 →
$67.06 against actual $411.34); top-decile net-load ex-tail −3.569 → −3.477
(+0.092); **remainder +1.451 → +1.452 (+0.001 — the body is untouched, the
raise-only anchored design held exactly)**.

**Δ-channel re-run on the arm (2025, `_miso180_structural_reports.json`):**
gap $5.28 = **Δ₁ identity +10.45** + Δ₂ cost level −6.44 + Δ₃ above-cost
+1.27. At the keeper: +10.50 / −6.44 / +1.27. **Δ₁ did not collapse — it
moved 0.5 % of itself.** The price-setter's identity is unchanged: the model
still clears efficient units (and imports) where the market cleared
expensive gas.

**The South dipole (the rule-1 falsifiable prediction — FAILED):** 2025
own-error, control → arm: East −15.16 → −15.05, Indiana −15.09 → −14.98,
Illinois −4.29 → −4.17, West −9.45 → −9.36, Plains −6.82 → −6.71,
**South +16.96 → +17.15 — away from zero.** The graft steepened the
Midwest stack top and the South over-price got marginally WORSE (the graft
raises South units' top tranches too, and the RDT premium posture is
unchanged). The ex-ante §1 statement applies verbatim: an arm that leaves
the dipole intact has not captured the real object.

**Price cuts:** annual dw deltas +$0.016 / +$0.003 / +$0.054 (2023/24/25);
JJA-only +$0.055 / +$0.005 / +$0.190 — concentrated in summer as designed,
and small. 2024 shows 2,706 differing hourly cells with ~zero net delta
(marginal-tie reshuffling around its six existing ≥$500 ceiling hours).
C3c tail counts essentially unchanged (2023: 4 → 5 model hours; 2024/2025
identical) — reported at full magnitude, still the ledgered model-class
limitation.

## 4. Why it is inert — the structural reading

The mechanism did everything its design promised: raise-only, body-blind,
rank-preserving, ceiling-respecting, and its offers reached $444–479 at the
stack top. It failed to matter because **the model's clearing point almost
never reaches the grafted region, and when demand pushes toward it the LP
substitutes around it** — imports, committed mid-stack supply, storage —
exactly the channel the static predictor declared absent (its 4.5×
overstatement is the measurement of that channel). The clearing rank stays
at r\* ≈ 0.44–0.48 mean (p90 of r\* = 0.62–0.69, vs the graft at > 0.875).
Raising the price OF the top of the stack cannot fix a model whose defect is
that it never NEEDS the top of the stack: the 88-hour tail is met with
−5.3 GW less gas and +2.1 GW more imports than reality (miso-178 §5), so
the marginal identity (Δ₁) — WHO sets the price — is untouched by WHAT the
un-dispatched units would have charged.

This inverts the dispersion-family diagnosis cleanly: after miso-179
(level form R: the model's body is +$15 OVER the book) and miso-180 (spread
form I: the correctly-anchored, correctly-sized top-decile rise binds
nothing), **the 2025 summer residual is not an offer-surface object at any
grain.** It is a supply-side object at the binding hours — the phantom
mid-stack surplus, of which the named, evidenced half is the seam import
excess (+2.1 GW at the 88 hours, the miso-176 FFE physics) awaiting the
D-2 5(i) admissibility ruling, with the South under-export (D-3) its
smaller sibling.

## 5. What this closes and what it opens

* **CLOSED: the across-unit dispersion family, both forms.**
  `miso_offer_level_dispersion` R (miso-179);
  `miso_offer_spread_anchored` **I** (this session — armed, measured, both
  runs registered). The field stays in the codebase, default off, correct
  and available; re-opening either form requires new evidence (a changed
  book, or a model whose clearing rank reaches the top decile — i.e. AFTER
  a mid-stack repair, when the same graft would bind; the sequencing logic
  of miso-178 §7 lever 2 applies to this lever too, in reverse).
* **OPEN, sharpened: D-2** — the seam-response envelope ruling. The reach
  argument strengthens: with the offer family exhausted, the import excess
  is the largest named object standing between the model and the
  DA-reachable surface (−13.71 pp of space; miso-178 §3). **D-3** (South
  under-export evidence) stands; the dipole datum here (+17.15 % with a
  steepened Midwest top) says the South symptom does NOT resolve through
  the offer stack. **D-4** (posture) unchanged.
* The keeper stands at `2026-08-22-miso-177-rho-measured`, NOT-YET on
  C3a-2025 alone.

## 6. Disclosures

1. **A/B scorer C8 leg corrected before adjudication:** the first scoring
   pass counted the criterion's non-gated `hydro: SKIPPED` rows (identical
   on keeper, control and arm) as failures — an over-strict reading that
   would fail the keeper itself; corrected to the criterion's own PASS
   semantics (gated records only) and re-run. No gated record differs.
2. **Arm attestation** generated from the keeper's
   (`scripts/gen_miso180_attestation.py`, the gen_miso169 precedent): two
   measured entries appended, `n_residual` unchanged at 2. The control
   stays UNATTESTED by convention (controls are never keeper candidates).
3. **Formatter-hook import incident:** the first control launch crashed at
   the new seam (`NameError`) because the format pass stripped the
   then-unused import added ahead of its call site; restored at `1f5adf7`,
   control relaunched. No partial bundle survived.
4. **Registration prunes:** the top-15-per-ISO retention removed
   `2026-08-16-miso-160-wefor-shape` and `2026-08-19-miso-169-control`
   (registry + payload + bundle) — the sanctioned sweep, committed with the
   registrations.
5. The manifest-digest prereg amendment (§1) — executed at intent level,
   strictly stronger content checks, both digests recorded.
6. Congestion caveat carried from miso-179: pooled H\* statistics are
   ISO-level (31.2 % of H\* hours congested); the anchor is a copper-plate
   identification. The A/B, which is fully zonal, is the adjudicator.
7. Rule 22: 2023–2025 only; MISO holds neither marker; freeze untouched.
   LOO at promotion is moot (no promotion); the identification is
   inputs-only with zero fitted parameters either way.

## 7. Reproduction

```
python3 scripts/data/fetch_miso_energy_offers.py            # 552 zips, ~430 MB
uv run --no-project --with pyarrow,pandas,numpy,pydantic,scipy,openpyxl,pyyaml \
  --python 3.12 python scripts/data/curate_miso_energy_offers.py --markets da
uv run --no-project --with pyarrow,pandas,numpy,pydantic,scipy,openpyxl,pyyaml \
  --python 3.12 python scripts/probes/_miso180_anchored_spread_precheck.py
# A/B (15 GB recipe, python 3.11, pinned stack, solves ALONE):
python3 scripts/replay_keeper.py results/calibration/miso177_rho_B \
  --out-dir results/calibration/miso180_anch_A --note "miso-180 CONTROL: ..."
python3 scripts/replay_keeper.py results/calibration/miso177_rho_B \
  --out-dir results/calibration/miso180_anch_B \
  --set miso_offer_spread_anchored=true --note "miso-180 ARM: ..."
python3 scripts/gen_miso180_attestation.py
uv run ... python scripts/probes/_miso180_ab_gates.py --identity ... --gates ...
uv run ... python scripts/probes/_miso180_structural_reports.py
```

Records: `_miso180_anchored_spread_precheck.json`, `_miso180_ab_gates.json`,
`_miso180_structural_reports.json`; bundles `miso180_anch_A` / `_B`
(registered `2026-08-23-miso-180-control` / `-anchored`). PREREG:
`PREREG-miso180-anchored-spread-2026-08-23.md` (commit `14ea321`).
