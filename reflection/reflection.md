# Reflection

Despite using the same source dataset, the three pipelines produced noticeably different outputs once requirements and tests were generated. The manual pipeline was more selective and detail-heavy, the automated pipeline was faster and more uniform, and the hybrid pipeline was the one that balanced both speed and clarity.

Through direct comparison, the clearest personas came from the hybrid pipeline. The automated personas were structurally complete, but a few descriptions included broad phrasing and assumptions that were not always strongly grounded in evidence. In contrast, the hybrid personas preserved the automated structure while tightening wording around actual review signals.

When focusing on requirement quality, the most useful requirements also came from the hybrid pipeline. Manual requirements were often thoughtful but more variable in style, while automated requirements were consistent yet sometimes vague in acceptance language. After selective refinement, the hybrid set was more testable and easier to map to concrete scenarios.

In terms of traceability strength, all three pipelines performed well at the metric level. Each one achieved full requirement-to-persona and requirement-to-test coverage in the final outputs. Even so, the hybrid pipeline had the strongest practical traceability because links were not only present, but also easier to interpret during review.

The main problems in automated outputs were not missing sections, but wording quality. Several requirements were grammatically correct yet used vague terms that weakened implementation precision. Some automated persona statements also overgeneralized user intent beyond the strongest review evidence. Overall, this is why the hybrid approach worked best: automation handled scale, and targeted human edits improved specificity where it mattered.
