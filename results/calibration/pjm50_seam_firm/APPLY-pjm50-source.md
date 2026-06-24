# pjm 50 core source edits — apply note

The three localized edits below (+207 lines total) implement the firm-export
floor + TVA/LGEE seams + losses-only hurdle. They live in large shared core
files, so they are committed here as a git-applyable patch (`pjm50_source.patch`)
rather than by re-emitting the whole files. The git proxy in the build
environment categorically rejects `git push` (HTTP 413 on git-receive-pack, even
a 16-byte pack), and the GitHub MCP `push_files` only takes whole-file content;
re-transmitting 8000 lines of unchanged core code by hand to add 207 lines would
risk corrupting working code, so the patch is the safe channel.

Apply on top of `origin/main` (verified `git apply --check` clean):

```
git apply results/calibration/pjm50_seam_firm/pjm50_source.patch
```

Files touched:
- `src/market_sim/config/constants.py` (+119): `NeighborInterface.firm_export_floor_by_year`
  field; TVA + LGEE neighbors; MISO/NYISO firm floors; hurdle 2.0->1.0 on all PJM
  seams; updated doc comments.
- `src/market_sim/model/transmission.py` (+76): `inject_reference_price_firm_export`.
- `scripts/run_calibration.py` (+12): import + call of the firm-export injector in
  the solve loop.

The authoritative source is also in local commit `cad552b` on this branch.
