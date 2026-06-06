# SUBMISSIONS — finals state (2026-06-04)

## SHIP THIS TO FINALS
**`v_final.zip`**  — sha256 `b108eff59b46b713fdfb1530f73eaeaa924f5dd9cb5ed72d3e63512a9ce3c36b`
- Leak-PATCHED build (closes the Qual-II near-dead stack-off; folds the red-team
  discriminator states the live R2 build jams).
- Status: validator PASS + edge-guard PASS. CAVEATS: UNBENCHMARKED, Docker smoke
  not yet run, source not committed to git. See verification TODO in
  `STATUS.md [FINALS-RECON]` and `docs/investigations/finals-prep-postmortem-2026-06-04.md`.
- Editable source of THIS zip: `archive/finals-ship-b108eff5-editable-source/`.

## Verify before upload (always)
    shasum -a 256 submissions/v_final.zip   # must be b108eff5...
    python3 ext/fullhouse-engine/sandbox/validator.py submissions/v_final.zip

## best_green.zip (kept here by policy — NOT the finals ship)
`best_green.zip` (sha256 `e4b4a8f1...`, the SIMPLE build) is the zero-risk fallback,
preserved at this path per the artifact policy + pre-commit hook. It is weaker
(Q1 #85) and has no post-R1 patches. Only ship it if v_final.zip fails final verification.

## Everything else is in archive/ (nothing deleted). See archive/README.md.

UPLOAD IS HUMAN-ONLY. No agent uploads. Verify the SHA of the exact bytes you upload.
