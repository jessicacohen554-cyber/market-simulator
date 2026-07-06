# HP-05 — Final adversarial extraction QA + signoff

**Model:** Opus · **Depends on:** HP-01–HP-04 (run last)
**Targets:** read-mostly audit; small fixes anywhere in `scope2-lce-portfolio/`;
`docs/handoff/SIGNOFF.md` (new)

Paste the block below into a fresh Claude Code session on
`jessicacohen554-cyber/market-simulator`.

```text
You are the final QA reviewer for the standalone Scope 2 LCE portfolio tool
in scope2-lce-portfolio/ (repo jessicacohen554-cyber/market-simulator).
Develop on a fresh branch off latest origin/main named scope2/hp-05-final-qa
(or your session's designated branch); push there; open NO pull request.
Adversarial mindset: your job is to BREAK the handoff claim — "this folder
can be pulled out of the repo and run independently as a complete,
documented tool" — then fix what you break (small fixes inline; anything
structural gets written up, not hacked).

AUDIT PASSES (do all six; record findings per pass)
1. EXTRACTION. Copy scope2-lce-portfolio/ to a temp dir outside the repo.
   Fresh venv from requirements.txt only. Run scripts/verify_standalone.sh
   AND, independently of it, repeat its steps by hand (the script itself is
   under audit). Then go beyond it: run the launcher, queue a real-ISO run
   from bundled data via the HTML form flow (HTTP calls, no browser), check
   the runs browser lists it and its cached report renders. Search the
   extracted copy for ANY runtime reference that escapes the folder
   (grep for ../, absolute repo paths, parents[N] escaping the tool root,
   market_sim, docs/codebase-site) and confirm each hit is build-time-only
   and documented.
2. ISOLATION & VENDORING. No `import market_sim`. Every vendored module's
   header still names upstream file + commit + re-sync procedure; spot-check
   one vendored function against upstream for silent drift.
3. DATA CONTRACT. Fill each committed template (all three) with small
   synthetic data and push them through intake and a full run: facility
   auto-aggregation sums correctly; missing-hour/duplicate/non-finite errors
   fire with their documented messages; the annual-average run carries its
   flat-price label through metadata, report, and launcher badge. Bundled
   data: every file has a provenance sidecar and every documented gap (ISO
   missing an LMP or CO2-rate file) is real and stated, not silently absent.
4. DOCS TRUTH. Every command in README.md, PLAN.md, docs/how-it-works.md,
   data/templates/README.md, launcher/README.md, docs/site/*.html runs as
   written from a fresh shell (in the extracted copy where the doc claims
   standalone). Every path referenced exists. Test counts and status claims
   match reality. Site pages have zero external references and render from
   file://.
5. LAUNCHER POSTURE. Loopback-only bind; request-size cap; run-id/path
   regexes; attempt directory traversal on /reports/ and every route added
   by HP-03; attempt an oversized POST; confirm friendly-error purity (no
   tracebacks to the browser). Confirm launcher state files and run log are
   gitignored.
6. RESULTS STORE. Committed results/ bundles: metadata schema consistent,
   reports re-render byte-stable where the existing test claims so, nothing
   gitignored-but-required.

FIX POLICY
- Small, low-risk fixes (broken link, stale sentence, missing gitignore
  line, an error message that lies): fix inline, with a test where the
  class of bug can recur.
- Anything requiring design judgment (LP semantics, ADR conflicts,
  launcher architecture): do NOT fix; document precisely in the signoff
  with a proposed approach.

DELIVERABLE — docs/handoff/SIGNOFF.md
- verdict: SHIP / SHIP-WITH-NOTES / BLOCKED (one line, first line);
- the six passes with findings: severity, what was fixed (commit), what
  remains open;
- exact reproduction of the extraction test output (trimmed);
- the final inventory: file tree summary, bundled-data table, test count.
Also tick the handoff table in docs/handoff/README.md rows that this audit
confirms, and correct any row it refutes.

RULES
All tests green after your fixes (python -m pytest tests/ -q). No
`import market_sim`. Small imperative commits rebased on origin/main; git
push; on a single 413 switch to mcp__github__push_files. No PRs, no raw
model IDs in commits/code. End with the verdict line + findings summary.
```
