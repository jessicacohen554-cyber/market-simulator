# PRE-REGISTRATION ADDENDUM — caiso-152: the corpus changes from 358 sampled days to the full contiguous span

**Written and committed BEFORE any value on the new corpus existed.** The
original pre-registration (`PREREG-caiso152-dam-bid-rle-parse-2026-08-01.md`)
is **not edited** — it stays frozen exactly as written, including its §3 corpus
clause, which this addendum supersedes on one point and one point only. The
**triggers in §4 are unchanged**, and no threshold, gate or reject condition is
touched.

---

## §A — what changed, and why it is not a choice

PREREG §3 registered a **358-day seasonally balanced** corpus (days 2, 5, 8,
11, 14, 17, 20, 23, 26, 29 of every month of 2023–2025), imported from the
caiso-150/151 intertie lane where corpus balance is load-bearing (caiso-150 §B).
That corpus was fetched — 358/358 days, 119/120/119 per year, 9–10 days per
(year, month), **zero archive holes** — and both arms were curated and derived
on it.

**Both arms FAIL the deriver's own G1 gate, identically**, and neither
reproduces the committed keeper artifact:

| statistic | OLD arm | NEW arm | committed (2026-07-19) |
|---|---|---|---|
| CC_REGULAR bucket | 7,964 MW (ratio 0.581) | 7,381 MW (0.538) | 13,454 MW (0.981) |
| CT_PEAKER bucket | 1,297 MW (**0.170**, bound ≥ 0.50) | 1,342 MW (**0.176**) | 10,785 MW (1.416) |
| CC_REGULAR econ_low | 1.645 | 1.649 | 1.051 |
| CT_PEAKER committed band | −0.278 | −0.281 | 1.155 |

**Identical failure on both arms is the diagnostic.** A defect that fires the
same way with and without the parse fix is not the parse. G1 is a gate, never a
trigger (PREREG §4), so no trigger has been read off these numbers and none is
carried forward.

## §B — the measured cause: this derive is a time-series estimator, and the balanced sample starves it

`derive_caiso_offer_surface.py` identifies gas resources by regressing **each
masked resource's daily body bid on the citygate daily series**, keeping only
resources that clear `r ≥ 0.6`, a slope in [4, 18] MMBtu/MWh, and ≥ 120
resource-days. That is a **per-resource time-series** estimator. Thinning the
corpus starves it, and the deriver's own G1 bucket capacity is strongly
monotone in trade-day count (measured, `density` subcommand, OLD arm):

| local trade days | resources scored | gas-pass | CC bucket | CT bucket |
|---|---|---|---|---|
| 122 | 257 | 54 | 4,303 MW | 414 MW |
| 179 | 458 | 81 | 5,253 MW | 1,135 MW |
| 358 | 570 | 99 | 7,964 MW | 1,297 MW |

The dominant failure modes are exactly the noise-driven ones — slope out of
[4, 18] (373 of 570 resources at 358 days) and `r < 0.6` (360 of 570) — not a
structural exclusion.

**The caiso-150 §B corpus rule is not transferable to this derive, and this
addendum does not weaken it.** The intertie ceiling is a
(month × hour-of-day) **climatology**: a sparse, seasonally balanced sample
serves it well, and a season-biased one wrecks it (~50 % headline overstatement,
mislocated peak). The offer surface is a **per-resource daily regression**: it
is indifferent to seasonal balance in the way the climatology is not, and
sensitive to day *density* in the way the climatology is not. Nothing in
caiso-150 §H is reopened — that DO-NOT-REDO governs the intertie ceiling, which
this session does not touch.

## §C — the corpus registered from here

**The full contiguous 2023–2025 span**, i.e. exactly what
`scripts/data/fetch_caiso_public_bids.py` produces with no arguments — the
deriver's *default* corpus, and what its frozen gates presuppose. The 358
balanced days are a subset of it and are re-used, not discarded; only the
remaining days are fetched.

This is a **superset** of the registered corpus, chosen because both arms
failed a gate on the subset, and its direction (more data) is not
outcome-selective: it was fixed before any value on it existed, it applies
identically to both arms, and no arm-specific choice is made anywhere.

## §D — what is unchanged, explicitly

* **The triggers.** T1 (6 consumed static band multipliers) and T2 (per
  class × net-load-bin mean rung), both at the deriver's own
  `max(0.08, 10 %)`, exactly as PREREG §4 froze them.
* **The comparison design.** OLD-parse vs NEW-parse on the SAME corpus, the
  OLD arm reproduced by identity-patching the shared expander. The committed
  artifact remains context only, never the control.
* **The third outcome stands.** If the corrected parse still fails G1–G4 on the
  full corpus, the lane STOPS at the derive, the keeper keeps the artifact it
  has, and **no gate threshold is retuned to rescue a verdict** (rule 23
  `[R-FROZEN-DERIVE]`).
* **Every reject condition and protective check** in PREREG §6/§7, and the
  1.0 pp C3a materiality trigger in §8.

## §E — what may NOT be claimed later

* That the 358-day result says anything about the **parse**. It does not — both
  arms failed the same gate the same way. Its only finding is §B's, about the
  corpus.
* That any 358-day multiplier is a measurement of CAISO conduct. Those numbers
  come from a starved classifier (CT bucket at 17 % of fleet, a negative
  committed-band multiplier) and are reported **only** as evidence that the
  corpus was inadequate.
* That the corpus was widened because a trigger did not fire. No trigger was
  evaluated on the 358-day arms, and this addendum was frozen before the full
  corpus finished fetching.
