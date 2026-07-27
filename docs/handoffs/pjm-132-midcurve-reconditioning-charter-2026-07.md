# CHARTER — pjm-132, executing the authorized within-season re-conditioning

**Lane:** `docs/handoffs/pjm-frontier-path-2026-07.md` §3c — the last named
admissible mechanism.
**Authority:** `docs/handoffs/pjm-midcurve-reconditioning-memo-2026-07.md`,
**AUTHORIZED WITH AN AMENDMENT** by the owner 2026-07-27 (decision banner in
the memo). Predecessor: pjm-131
(`results/calibration/FINDING-pjm131-gate1-no-admissible-arm-2026-07.md`).

This charter is committed **before** the re-derive is run and before any solve.
It **inherits memo §4's gates verbatim** — it does not restate them loosely and
does not add, soften or re-scope a single criterion.

## 0. Settled going in — not re-litigated

The corrected CAMPD envelope stays in (rules 1 / 14). Gate 1 is displacement,
measured. **Gate 1's CC_CHP half is not independently armable** — pjm-131
measured κ = 0.023 at 72.7 % mean utilization, so CC_CHP clears on price, not
capacity; it is the same merit-ownership question as gate 2 and is carried by
*this* lever, not a separate one. ST_GAS is grounded (D-4 pass, 0.000
off-window). Gate 3's root cause is out of reach and is ledgered. Lane 2's
commitment-status half is closed terminal (pjm-128). `chp-btm-share` is globally
degenerate and is NOT repaired or wired here (pjm-131 §3). Holdout freeze active:
2023–2025 only (rule 22). Keeper `2026-07-25-pjm-121-cc-belt` is owner-only.

## 1. The owner amendment — what changes vs memo §2

Memo §2 proposed the new vintage take over the **live filenames**. The owner's
term — *"keep the current config as default unless seasonal is new keeper"* —
supersedes that clause and only that clause:

* **Within-year surfaces stay live and keep their filenames.** They remain the
  default for every keeper and every forecast run.
* **The within-season vintage is written to new, separately-named artifacts.**
  Nothing existing is renamed, retired or deleted.
* **One default-OFF `ScenarioConfig` gate** (rule 24 `[R-REGISTRY]`) selects the
  whole family coherently: JSON vintage **and** solve-time seasonal binning
  move together, never independently.
* **Vintage guard, strengthened to the pairing.** An armed gate reading a
  within-year JSON, or an unarmed gate reading a within-season JSON, **hard-fails
  the solve**. A half-updated state cannot silently mismeasure.
* **Byte-identity requirement:** with the gate off, every solve must be
  byte-identical to today. This is verified before the A/B, not asserted.

Memo §2's other clauses stand unchanged: **both** surfaces move as one
definitional vintage in one commit; both consumption seams change coherently;
all mid-curve consumers inherit the seam; **no other ISO is touched** (rule 25).

## 2. Season definition — fixed in advance, unchanged

Memo §3, i.e. `pjm126_midcurve_conditioning_precheck.SEASON_OF_MONTH` (committed
`9409f7f` before any result was seen): **summer** Jun–Sep, **winter** Dec–Mar,
**shoulder** Apr–May + Oct–Nov. Ranking is within (year, season). **No boundary
is moved**; any future proposal to move one needs its own memo first.

## 3. Stage 1 — re-derive + no-LP pre-check (NO solve)

Re-derive both surfaces within-season (same edges `[0.80, 0.90, 0.97]`, same
share grid, same segmentation, same gas normalisation — **only the ranking scope
changes**), then run the pre-check on the keeper fleet reconstructed via
`scripts/lib/bundle_fleet.py` (**not** `_run_year_kwargs`).

**Pre-registered expectation** (memo §4, from pjm-126/127 arm B — predictions
about the derive output, checkable before any solve): armed-segment bin3 ladders
RISE relative to the within-year vintage (CC_LIKE body ≈ +0.4–0.5 × gas in
2025); bins 1–2 FALL modestly (≈ −0.1 × gas); LONG_RUN approximately unchanged;
CT_FAST bin3 rises sharply (≈ +10 × gas) but CT_FAST is **not armed** in the
keeper's floor scope (rule 19 — owned by the pjm-103 startup amortization).

**K1-gradient kill (the pjm-123 criterion), unmet-means-dead:** the new
surface's MW-weighted bid delta on the keeper fleet must be **larger in the
tightest bin than in the slackest** (gradient bin3 − bin0 > 0) for the **armed
floor scope**, in **at least 2 of 3 years**. A surface whose re-conditioning
still moves the slack bins as much as the tight bin is not a dispersion lever
and **no solve is spent**.

**Honesty bound (reported to the owner BEFORE spending the chain, not after):**
if the armed tight-bin floor rises by **less than ~$1/MWh MW-weighted**, the
expected solve-level effect is within noise — that is reported as such before
Stage 2 is launched.

## 4. Stage 2 — the A/B solve chain (ONLY if Stage 1 survives)

Keeper recipe vs keeper recipe + the re-conditioned surface (+ the coherent seam
change), via `replay_keeper.py results/calibration/pjm121_ccbelt`, **all of 2023
2024 2025 in ONE bundle** (rule 16), years sequential, one fresh process per
solve-year (rule 12; single-year peak 14.87–15.06 GB on a 15.7 GB box — NEVER two
PJM years concurrently). Full determination scoring. **Registered on the
dashboard win or lose** (rule 15).

**PASS signature (adopt) — all of:**
1. the 2025 C3a gain is carried by the **tight strata**: on the pjm-120 stratum
   decomposition (baseline 2025: 0–25 +2.015, 25–50 +2.249, 50–100 −3.662,
   100–200 −2.487, 200–376 −1.126, >376 −1.534 $/MWh), the combined **≥$50**
   strata contribution improves by **more than** the combined **<$50** strata
   contribution moves;
2. model hourly price dispersion widens toward actual (p90−p10 up, weekly CV up);
3. **C1 stays 16/16 gated rows, all years** (the pjm-108 failure mode — CC
   displacement — is the known risk of raising the CC floor);
4. every other closed gate stays closed;
5. the verdict flip, if any, survives **leave-one-year-out within 2023–2025**.

**REFUTATION signature (closes the family for good):** the effect is a **level
shift either way** — the stratified delta is near-uniform across strata
(price-gradient ≤ 0), **or** C3a moves while the tight-strata gap does not close,
**or** C1 breaks. The measured-offer-surface family will then have been tried as
a dispersion lever under **both** conditioning definitions; **Lane 2 ends**, and
with Lane 1 already complete the frontier ledger is whole.

**Either outcome is registered** (keeper candidate or rejected probe, same
session). **Promotion is flagged, never taken** — `keepers.json` is owner-only,
and under the §1 amendment the default only flips if the owner promotes.

## 5. What may NOT happen under this authorization

Memo §4's closing clause, binding: **no edge re-tuning, no share-grid change, no
segmentation change, no new free parameter.** The re-derive changes the ranking
scope and nothing else. No other ISO's surface is touched (rule 25). No holdout
year (rule 22). No `keepers.json` edit. No CI job for a solve. `chp-btm-share`
is not repaired or wired here. Any post-hoc correction to a pre-registered
formula is disclosed at the site **and** in the finding (pjm-131 §4 precedent).

## 6. Scope constraint found during execution — the top-of-curve surface cannot be migrated

**Reported before the chain was spent, per memo §4's honesty clause.**

Memo §2 requires both surfaces move as ONE definitional vintage, precisely so a
future session arming the dormant top-of-curve mechanism cannot stack a
within-year surface on a within-season one. **That is not achievable in this
session, and no workaround was taken.**

The committed `pjm_offer_surface_condbinned.json` records its base-HR
normalisation basis as the **`pjm98_cc_mustrun`** bundle (fleet year 2024). That
bundle is **absent from disk and absent from git** — only its archived run
driver (`scripts/archive/run_pjm98_cc_mustrun.py`) survives, and the derive
needs the bundle's `meta.json` to replay the fleet. Re-deriving the top-of-curve
surface against any other bundle would change the **fleet basis** as well as the
ranking scope, which memo §4's closing clause forbids ("the re-derive changes
the ranking scope and nothing else"). A surface derived that way would not be
comparable to the vintage it replaces, and the drift would be invisible because
the mechanism is dormant.

**What was done instead:**

* The **mid-curve** surface — the armed mechanism, the entire lever, and the
  only one the A/B measures — **is** re-derived within-season exactly. Its
  derive takes no fleet bundle (`--years`, `--edges`, `--conditioning` only), so
  it is a true like-for-like: only the ranking scope changes.
* The **top-of-curve** surface stays within-year and **is not touched**.
* The half-migrated state is made **unreachable rather than silent**: an armed
  `pjm_offer_surface_within_season` whose vintage artifact is missing now raises
  `FileNotFoundError` instead of degrading to "mechanism off". Arming the
  dormant top-of-curve mechanism together with the seasonal gate therefore
  hard-fails until its within-season vintage exists.

**Consequence for the A/B: none.** `pjm_offer_surface_conditional` is OFF in the
keeper, so the top-of-curve surface does not enter either arm; Stage 1 and
Stage 2 measure the mid-curve change, which is exactly the "armed floor scope"
memo §4 pre-registered.

**Owner decision deferred, not assumed:** completing the family migration needs
the `pjm98_cc_mustrun` basis restored (or an explicit authorization to re-derive
the top-of-curve surface on a new basis, which is a *different* change needing
its own case). Flagged here; not taken.
