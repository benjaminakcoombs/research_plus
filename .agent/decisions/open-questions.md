# Open Questions

<!-- Unresolved questions with TL;DR summary. -->

## OQ-1: Calibration example data leakage (2026-03-16)
`prompts/situation_assessment/calibration_examples/healthcare_services.md` uses Acadia Healthcare as the example company. If we run the pipeline on Acadia, the model sees the "answer" in the calibration prompt. Need to either anonymize the example or swap to a different healthcare company.

## OQ-2: `{TARGET_BANK}` not flowing through full prompt chain (2026-03-16)
The `--target-bank` CLI flag is consumed in L0 but doesn't propagate as a first-class variable into L1.5, L2, or L3 prompts. For situation_assessment mode, bank-specific context (coverage strengths, recent deals, sector focus) could sharpen the output significantly. Decision needed on whether this is worth the added complexity.
