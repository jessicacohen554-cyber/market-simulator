# FINDING — capx D38: D36's routed records land — the NEISO FC-5 storage rows are re-authored with the procurement-channel driver plus the R-1 residual, and golden-2 §6.1's rank misattribution is annotated

**Lane:** records-only execution of `FINDING-capx-d36-storage-valuestack-2026-09-02.md`
§8 routed items 1 and 3. **Zero solves, zero scorer edits, zero verdict moves.**
Two files touched, both text.

## 0. What changed (the whole diff)

| File | Change | Diff |
|---|---|---|
| `results/ff-corridor/dispositions/neiso-t3.json` | the `explanation` string of the three `capacity:storage` rows (2030 / 2035 / 2040), re-authored per D36 §7 | 3 lines changed (3+/3−) |
| `docs/handoffs/FINDING-capx-t3-golden2-2026-09-01.md` | one dated annotation appended at §6.1 | 21 lines added, 0 removed |

Nothing else. No scorer, no FC row definition, no board, no keeper/shard/marker,
no `ScenarioConfig`, no matrix shard, no new workflow.

## 1. Item 1 — the three `capacity:storage` rows

**What the prior wording did and did not do.** The row read "the arbitrage+RA value
stack clears no tech at the anchor years … the battery fleet is still the 0.77 GW
EIA-860 base" — true, and D36 §7's own objection to it is that *it attributes
nothing*: it states the screen's outcome without naming the driver of the −56.2 %
divergence or the model-side residual. D36 §7's recommended text is the
disposition transcribed here: **procurement channel unrepresented (the D25 §4.3
mechanism-3 instrument family), with the merchant stack's own arbitrage blindness
(R-1) as the model-side residual.**

**What the new text says**, in D36's own terms and citing it:

- **The driver** — no state-procurement build channel for storage. AEO2025 carries
  New England's procurement obligations as policy inputs (the MA 2024 climate
  statute's 5,000 MW-by-2030 storage directive, CT Public Act 21-53's 1,000 MW
  target, the MA Clean Peak Energy Standard credit stream — each an enforceable
  public instrument to confirm at intake, each a dated MW obligation and so
  formulaic in the rule-13 sense). The model builds storage only through the
  merchant economic screen, so a contracted obligation has no way in; were the
  channel ever chartered it enters as a known-additions row (step 4), never
  through the screen.
- **The model-side residual (R-1)** — the arbitrage leg is the short term in every
  year by $50–150/kW-yr, the RA leg second-order (and D33's object, not a second
  storage mechanism). With the RA leg at maximum and the arbitrage leg at the real
  ISO-NE market's best year, li-ion 4 h is short in every year. The identified
  route is the gated default-OFF `entry_forward_expectation_signal` (NEISO cell
  `U`) — an entry-signal mechanism moving every capacity screen, not a storage one
  (rule 19) — with `entry_screen_diagnostics` as its zero-cost precondition.
- **The 2050 entry**, retained from the prior text and re-attributed: 720 MW of
  100-h iron_air, after the anchor window, a data-channel result of the RC-R
  re-timed exits, not a D-3-rank result (see §2).
- **The control facts are retained verbatim in substance:** the armed posture
  (`storage_entry_availability_gate` / `storage_entry_cost_normalized_rank` true,
  owner ruling R-A), the 0.77 GW base fleet at every anchor, the −56.2 % divergence
  UNCHANGED by the arming as a measured campaign result (T3-GOLDEN-2 §6), and the
  rule-13 line that the corridor number is context and never a target.

The three rows carry the same text, as they did before this edit and as the three
`capacity:wind_total` rows do — the explanation is year-agnostic and the anchor is
identical at all three target years.

## 2. Item 3 — the golden-2 §6.1 annotation

Appended as a dated annotation, **never a rewrite**: the corrected bullet stays on
the page and is quoted inside the annotation, so the record shows what was said
and what supersedes it. Marked "Correction 2026-09-02 (D38, routed by D36 §8.3)".

The substance: golden-2 §6.1 attributed the 2050 clearing to the D-3
cost-normalized rank ("where the pre-R-A absolute-margin rank had cleared
nothing"). D-3 is **sign-preserving** by its own docstring (`storage.py:1789`) —
it reorders clearing technologies and can neither create nor remove a clearing —
and D-2 only removes candidates, so on identical prices the armed screen clears a
*subset* of the unarmed screen's clearers. The arming could not have produced the
entry. The clearing is a **data-channel** result, the channel §6.2 already
attributes the trajectory delta to: the RC-R demand-curve intake re-times the exit
waves, less capacity is retained, the out-year stack tightens (2049: 2,243 h ≥
$100/MWh vs golden-1's 1,339; 2050: 2,446 vs 1,531), and the iron-air requirement
crosses its arbitrage leg between the 2049 and 2050 screens ($83.4 → $78.7/kW-yr).
The rank chose *among* clearers, of which iron-air was the only one — never
decisive. Everything else in §6.1 is explicitly left standing.

## 3. The control check (item 1's guardrail)

**Before editing:** the working tree's `neiso-t3.json` was byte-identical to the
committed blob — `git hash-object` = `git rev-parse HEAD:…` =
`7c6750237f94c545db378afd762c7cfe7764a85a`. No pre-existing local drift to
preserve or clobber.

**How the edit was made:** programmatically, after proving the file round-trips
byte-identically through `json.dumps(indent=1, ensure_ascii=True)` (37,432 bytes
in, 37,432 out, `==` True), so re-serialization could not perturb formatting,
key order, or escaping anywhere outside the target strings. The script asserted,
before writing:

- exactly 3 rows with `quantity == "capacity:storage"`;
- each already `verdict == "EXPLAINED DIVERGENCE"` (a row in any other category
  would have aborted, per the charter's STOP condition);
- row count and row key-sets unchanged;
- the **only** differing fields across all 54 rows are the three
  `explanation` strings, on `capacity:storage` rows;
- every top-level key other than `rows` byte-equal.

**After editing** (all verified against the file on disk):

| Check | Before | After |
|---|---|---|
| rows | 54 | 54 |
| `IN CORRIDOR` | 28 | 28 |
| `EXPLAINED DIVERGENCE` | 26 | 26 |
| `UNEXPLAINED` | 0 | 0 |
| `counts` block | 28 / 26 / 0 / 54 | untouched |
| `git diff --numstat` | — | `3 3` |

`git diff` shows three `-`/`+` line pairs, all of them the `"explanation":` line
of a `capacity:storage` row. **No row changed category and no verdict moved,
here or anywhere else.** The FC-5 header's `counts` block needed no edit because
nothing it counts changed.

The schema did not resist the re-author: `fc5-disposition/v1` carries
`explanation` as a free-text string, and no script in the repo reads these
disposition files (they are the rubric's human artifact), so there is no
consumer to re-run or invalidate.

## 4. Rule 27

The golden-2 finding is ≥300 lines (584 → 605), so it was edited **locally**
with the Edit tool — never regenerated from response content — and the exact
on-disk bytes are pushed. Blob verification against the remote follows the push;
the local blob shas at the time of writing are
`462ec2a807ca002735cd3f130d941098f8ca59f8` (golden-2 finding) and
`cc8dbbe4a94e1109723dbf1501b750b9f7ffa8d5` (`neiso-t3.json`). The disposition
file is data, not source, and was likewise written whole from a verified
round-trip rather than retyped.

## 5. Governance attestation

Zero solves; no LP, no bench, no score, no registration — rule 15 does not fire.
No out-of-training year touched (nothing was solved at all). No `src/`, no
`ScenarioConfig` field, no mechanism tested or armed, so rule 28's matrix duty
does not fire — the two cells D36 named (`entry_forward_expectation_signal`
NEISO `U`, `storage_entry_*` NEISO `U`) are **read, not written**, exactly as D36
left them. No board, keeper shard, marker, FC-6 checker, or `ff-verdicts.json`
write; the FC-5 disposition file was this window's sole shared-file risk and D35
does not touch it. Rule 25 held: every number transcribed is NEISO's own. Rule 13
sign discipline is carried through in the new row text (R-1 named as the residual,
the corridor number named as context). No new GitHub Actions workflow.

**Still open from D36 §8, not this lane's:** item 2 (`entry_screen_diagnostics`
on the next NEISO solve, then the entry-signal lane's
`entry_forward_expectation_signal` NEISO cell), item 4 (D33 proceeds unchanged),
item 5 (R-3(a) learning-convention repair in `model/storage.py`, for whichever
lane next holds that file under its model assignment).
