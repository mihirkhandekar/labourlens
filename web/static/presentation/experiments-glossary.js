// Plain-English meanings for the short labels used on experiment cards. Each term lists a pattern; a card shows
// only the terms that appear in its own text, and the notebook shows the whole list once near the top.
// Wording describes the configuration only; no report text and no results are stated here.
export const GLOSSARY = [
  {group: 'Retrieval methods', term: 'BM25', re: /\bBM25\b/, text: 'Keyword search. Scores a chunk by how many of the question’s words it contains, giving rare words more weight.'},
  {group: 'Retrieval methods', term: 'Dense', re: /\b[Dd]ense\b/, text: 'Meaning search. Question and chunks are turned into lists of numbers (embeddings); chunks whose numbers point the same way rank first. The model is text-embedding-3-large unless a card says otherwise.'},
  {group: 'Retrieval methods', term: 'RRF', re: /\bRRF\b|reciprocal rank/i, text: 'Reciprocal rank fusion. Each ranked list gives a chunk 1 ÷ (60 + rank) points; points are added across lists. Uses ranks, not raw scores, because BM25 and dense scores are on different scales.'},
  {group: 'Retrieval methods', term: 'Hybrid / R0', re: /\bHybrid\b|\bhybrid\b|\bR0\b/, text: 'BM25 and dense lists fused with RRF (top 50 from each). No filter, no boost, no rerank. R0 is the name of this baseline in the R-series.'},
  {group: 'Retrieval methods', term: 'R1a', re: /\bR1a\b/, text: 'Hard period/release filter. The quarter and release stage (advance or final) named in the question are read out, both result lists are restricted to documents that match, then fused as in R0. No hint, or no matching document: nothing is filtered.'},
  {group: 'Retrieval methods', term: 'R1b', re: /\bR1b\b/, text: 'Soft boost. After fusing as in R0, a chunk from a document that matches a hint gets a small fixed bonus (0.5 ÷ 61, set in advance, not tuned). Matching documents rise but others can still appear.'},
  {group: 'Retrieval methods', term: 'R1b_x0.5, R1b_x2', re: /R1b_x0\.5|R1b_x2/, text: 'Sensitivity checks of R1b: half the bonus (.25 ÷ 61) and double the bonus (1 ÷ 61). Reported to show whether the boost size matters.'},
  {group: 'Retrieval methods', term: 'R2', re: /\bR2\b/, text: 'Rerank only. Take R0’s top 30 chunks and ask gpt-6-luna to return the labels of the most useful (at most 10), best first. Bad or unknown labels are dropped; on failure the old order is kept.'},
  {group: 'Retrieval methods', term: 'R3 / r3', re: /\b[Rr]3\b/, text: 'Filter, then rerank: R1a’s hard filter followed by R2’s rerank. “r3” is the same setting as selected in the agent. This is the retrieval setting the project adopted.'},
  {group: 'Retrieval methods', term: 'R3w / r3w', re: /\b[Rr]3w\b/, text: 'R3 plus widening: if the filter leaves fewer than 8 chunks, or the filtered best BM25 score is under half the unfiltered best, search is widened again. Tested and not adopted.'},
  {group: 'Chunking', term: 'blocks', re: /\bblocks\b/, text: 'Each source passage is its own chunk. Many very short chunks.'},
  {group: 'Chunking', term: 'mergeN (merge120, 200, 300, 400)', re: /\bmerge\d+\b/, text: 'Adjacent passages under the same heading are grouped until a word target N is reached, with whole-passage overlap of about 20 to 25%. Chunks never cross a heading or a source, so real chunks are shorter than N. merge200 is the runtime default.'},
  {group: 'Chunking', term: 'fixed150', re: /\bfixed150\b/, text: 'Fixed windows of about 150 words that ignore headings. A control to show whether respecting document structure matters.'},
  {group: 'BM25 settings', term: 'k1, b', re: /\bk1\b/, text: 'BM25 parameters. k1 controls how quickly repeated words stop adding score; b controls how much long chunks are penalised.'},
  {group: 'Metrics', term: 'hit@k', re: /hit@\d+/i, text: 'Share of questions where at least one labelled gold passage is inside the first k chunks. hit@8 is the headline cut-off.'},
  {group: 'Metrics', term: 'strict hit@8', re: /strict/i, text: 'Builds the real answer context (after removing duplicates) and checks only its first eight passages. Harder than chunk hit@8, because one chunk can hold several passages.'},
  {group: 'Metrics', term: 'MRR', re: /\bMRR\b/, text: 'Mean reciprocal rank: average of 1 ÷ (rank of the first relevant chunk). 1 means always first; 0 means never found in the cut-off.'},
  {group: 'Metrics', term: 'pool recall@30', re: /pool recall/i, text: 'Share of questions whose gold passage is inside the 30 candidates the reranker sees. It is the ceiling for reranking: the reranker cannot find what is not in the pool.'},
  {group: 'Metrics', term: 'Better / worse', re: /[Bb]etter\/worse|\bbetter\b.*\bworse\b/, text: 'On the same cases, how many improved and how many got worse between two settings. Cases that are unchanged are not counted.'},
  {group: 'Metrics', term: '95% interval', re: /\bCI\b|95%|interval/i, text: 'Bootstrap interval: resample the cases many times to see how much a score moves by chance. If an interval for a difference includes zero, no real difference is shown.'},
  {group: 'Metrics', term: 'McNemar', re: /McNemar/i, text: 'A paired test that looks only at cases where two systems disagree (one right, one wrong).'},
  {group: 'Answering', term: 'Behaviour accuracy', re: /[Bb]ehaviou?r/, text: 'Share of cases where the system chose the expected status: answer, abstain, clarify or refuse. It is scored by rule, without an AI judge, and it does not show that an answer’s contents are correct.'},
  {group: 'Answering', term: 'Always-answer floor', re: /floor/i, text: 'Score of a no-model rule that always answers. It shows how much of a score comes from the mix of question types rather than from skill.'},
  {group: 'Answering', term: 'oracle / G0', re: /\boracle\b|\bG0\b|reference passages/i, text: 'Control where the correct passages are placed in front of the model. It measures the model alone, without retrieval errors.'},
  {group: 'Answering', term: 'M3 G1, G3, G4', re: /\bG[134]\b|M3/, text: 'Early answer-generation experiments: G1 compares six models, G3 varies how many chunks (k) are shown to small models, G4 re-tests the cautious candidate at k=8.'},
  {group: 'Answering', term: 'gpt-6-luna', re: /gpt-6-luna/, text: 'The primary answering model used in the evaluated system.'},
  {group: 'Answering', term: 'answer_vN, planner_vN, triage_vN', re: /answer_v\d|planner_v\d|triage_v\d/, text: 'Version numbers of the saved prompt files in `prompts/`. Evaluated system: planner_v1 and answer_v3 unless a card says otherwise.'},
  {group: 'Agent runs', term: 'A1 to A5', re: /\bA[1-5]\b/, text: 'Development agent runs: A1 baseline (hybrid, answer_v3, planner_v1); A2 answer_v4; A3 r3 retrieval; A4 r3 with widening (r3w); A5 planner_v2.'},
  {group: 'Agent runs', term: 'FIN / FIN2', re: /\bFIN2?\b/, text: 'Two repeated final comparisons of hybrid against r3 with the primary model. The headline figure is their mean; both single runs are kept.'},
  {group: 'Agent runs', term: 'X1, X2, X3', re: /\bX[123]\b/, text: 'Regression checks after code changes: X1 extraction fixes, X2 new corpus and runtime fixes together, X3 a report-arithmetic tool set that was rejected.'},
  {group: 'Agent runs', term: 'V2, V2post, V31', re: /\bV2post\b|\bV31\b|\bV2\b/, text: 'Fresh-question set runs: V2 the first evidence-disjoint 65-case run, V2post a diagnostic after the freeze, V31 a rerun on corpus v3.1.'},
  {group: 'Agent runs', term: 'MCP', re: /\bMCP\b/, text: 'Model Context Protocol: the standard the agent uses to call tools hosted in a separate server process, which the client treats as untrusted.'},
  {group: 'Agent runs', term: 'S65 / served chain', re: /S65|[Ss]erved chain/, text: 'A 65-case sample run through the application path that users hit, not the frozen evaluation harness.'},
  {group: 'Case ids', term: 'DEV, HO, HO-V2, F2, SERVED, CX', re: /\b(DEV|HO|HO-V2|F2|SERVED|CX)-/, text: 'DEV-n development cases; HO-n the original registered held-out set; HO-V2-n and F2-n the fresh evidence-disjoint set; SERVED-Pn served-chain sample; CX-n conversation-context cases.'},
  {group: 'Threats', term: 'guarded / naive', re: /[Gg]uarded|[Nn]aive/, text: 'Guarded: the full system with its input scanner, quote check and defended prompt. Naive: the same model with the defences off.'},
  {group: 'Threats', term: 'T-I06', re: /T-?I06|TI06/, text: 'The planted-false-figure attack: a retrieved passage plants a wrong figure. The one attack not reliably stopped, and its result was unstable between runs.'}
];

export function termsIn(haystack) {
  return GLOSSARY.filter(entry => entry.re.test(haystack));
}
