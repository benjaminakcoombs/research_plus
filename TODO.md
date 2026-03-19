# Deep Analysis — TODO

## P0: Blocking or will cause errors

- [ ] **Write `l3b_refinement.md` for `strategic_briefing` mode.**
  The L3a/L3b split is implemented in code (`prompt_builder.py`, `orchestrator.py`, `models.py`) but `prompts/strategic_briefing/l3b_refinement.md` doesn't exist yet. Running `--mode strategic_briefing --run-all` will crash at L3b with a `FileNotFoundError`. Needs a refinement prompt tuned for the exec/consulting audience (CEO/COO reader, not banking MD).

## P1: Quality / correctness

- [ ] **Fix calibration example data leakage.**
  `prompts/situation_assessment/calibration_examples/healthcare_services.md` uses Acadia Healthcare as the example. Running the pipeline on Acadia means the model sees a pre-built answer in the calibration block. Either anonymize or swap to a different healthcare services company.

- [ ] **Verify `l3a_synthesis.md` for `strategic_briefing` mode is current.**
  The file was renamed from `l3_final_synthesis.md` but its content hasn't been rewritten to match the new Deep Analysis format. It may still reflect the older "executive briefing" structure. Needs audit and likely a rewrite to parallel the situation_assessment L3a quality.

## P2: Enhancement

- [ ] **Flow `{TARGET_BANK}` through the full prompt chain.**
  Currently consumed only at L0. Could improve specificity in L1.5 consolidation (weight tension points the bank would care about), L2 deep dives (research bank-relevant angles), and L3 synthesis (frame findings for that bank's coverage strengths).

- [ ] **Add `--dry-run` flag for cost estimation.**
  Before committing ~$40-70 per run, users should be able to see estimated cost and token counts per layer without actually calling the API.

- [ ] **Update `.agent/config.md` key files list.**
  The config still references old file names (`L3_final_synthesis.md`, `prompts_archive/`, root-level `.md` prompt files) that were reorganized. Should reflect the current `prompts/strategic_briefing/` and `prompts/situation_assessment/` structure, `docs/` folder, and L3a/L3b split.
