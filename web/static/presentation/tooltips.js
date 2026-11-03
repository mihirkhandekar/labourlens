// Deck popover policy. A popover is one short, plain idea. Whatever was longer is kept as a speaker note on the same slide,
// so nothing is lost. Pure functions plus a WeakMap of originals; no network and no HTML strings.

/** Words an automatic summary aims for, and the most any popover, title or label may carry. */
export const TIP_WORDS = 22;
export const TIP_MAX = 30;

export const wordList = text => String(text ?? '').trim().split(/\s+/).filter(Boolean);
export const wordCount = text => wordList(text).length;

// Hand-written summaries for popovers whose first sentence is not the useful one. Matched on the start of the original text.
// Each keeps the figure the slide is about; the original goes to the speaker notes.
export const OVERRIDES = [
  ['The statistics store covers 1980', 'The statistics store holds 11,228 in-scope rows for Q1 2020 to Q2 2026, and older history for context.'],
  ['Input: source, period range and dimension. Output: validated rows', 'You give a source, a period range and a dimension. It returns validated rows with their units and provenance.'],
  ['Input: a question and optional result limit', 'You give a question. The app searches the report index, filters by period and release, reranks and returns labelled chunks.'],
  ['Verified from the local current-build chunk', 'This chunk is from the Q1 2026 final report, pages 2 to 3: 216 words, nine source passages, one vector.'],
  ['Schematic, not a real report quotation', 'A schematic, not a quotation. A real table block in this report is flagged unreliable and excluded from search.'],
  ['Parser extract-0.3:', 'PyMuPDF reads PDF layout and BeautifulSoup reads web pages. Table-like blocks are flagged, not repaired.'],
  ['The live corpus (v4) has', 'The live corpus, v4, was not evaluated; the evaluated build, v3.1, had 85 sources. Only passages flagged ok enter search.'],
  ['The live runtime uses merge200', 'Chunks join neighbouring passages to about 200 words with 40 words of overlap, and are rebuilt in memory at startup.'],
  ['text-embedding-3-large produces 3,072-number vectors', 'Each chunk becomes a vector of 3,072 numbers. Unchanged text reuses its saved vector.'],
  ['BM25 indexes tokenised chunk text', 'BM25 indexes chunk words in memory. A saved index for different chunks is refused, not reused.'],
  ['Both indexes search the same chunks', 'Keyword and meaning rankings are fused, then filtered by period and release and reranked.'],
  ['Raw MOM and MTI PDF and HTML files', 'Raw report files stay on this machine. Only the manifest of hashes and sources is committed.'],
  ['BM25 with k1=1.5', 'Keyword search: 47.7% of 128 questions had a relevant passage in the top eight. It needs the exact words.'],
  ['text-embedding-3-large vectors of about 200-word chunks', 'Meaning search: 36.7% of 128 questions had a relevant passage in the top eight. It finds paraphrases, but mixes quarters.'],
  ['Hybrid: reciprocal rank fusion', 'Hybrid search: 53.9% hit in the top eight. It is not shown to beat keyword search alone.'],
  ['Input validation runs first', 'The served planner chooses four tools. The evaluated base set had three; annual averaging has not been evaluated.'],
  ['Inside the agent loop, the planner chooses one tool', 'The planner picks a tool. Report search runs in the app: keyword plus meaning, filtered and reranked.'],
  ['Only the statistics lookup uses MCP', 'Historically only statistics lookup used MCP. The served build also routes annual averaging through MCP; both are read-only.'],
  ['calculate_change uses deterministic Decimal', 'Changes are exact Decimal arithmetic on rows already collected. The model does not calculate.'],
  ['The planner can stop without calling a tool', 'The planner may stop early. The answer still goes through evidence and answer checks.'],
  ['Logical evidence checkpoint', 'After each tool call the planner sees new evidence and may go again while budget remains. Then conflicts are noted.'],
  ['Validate the structured answer', 'Citations, quotes and numbers are checked against the evidence. One failed answer is regenerated, a second is marked invalid.'],
  ['Final statuses also include', 'An answer can also end as a clarification or refusal. Errors and blocked output stay distinct from missing evidence.'],
  ['Base configuration: at most two', 'At most two evidence rounds, three calls per round and six calls overall.'],
  ['Six planned tool calls across the run', 'Six tool calls in total, run one after another. Only an on-time result is kept.'],
  ['Default agent tool deadline', 'Each tool call has ten seconds. A timed-out call is not retried and its late result is dropped.'],
  ['One retry for a JSON parsing failure', 'Only the structured planner retries malformed plan JSON. Native tool arguments fail as budget-counted errors. Answer repair remains separate.'],
  ['The app searches the passage index', 'The app searches the report index. The planner never sees passage text, only the answer writer does.'],
  ['Deterministic Decimal arithmetic checks', 'Exact difference or percentage change on rows already returned, with units checked. It cannot invent inputs.'],
  ['The application owns the agent', 'The app owns the agent and MCP client. The served planner has four tools; two use the statistics server.'],
  ['A persistent stdio session', 'One stdio session sends a typed request and checks the reply: schemas, 200 KB size cap and 8 second deadline.'],
  ['The server exposes nine read-only', 'The recorded server had nine tools and the agent used one. The current server has ten; the agent uses two.'],
  ['The highlighted tool is the agent integration', 'The served agent uses statistics lookup and annual averaging. Eight other server tools stay outside the planner.'],
  ['Resource template labourlens://source', 'One catalogue entry per source. It is a template, not a fixed address, and holds no report passages.'],
  ['Server to client: structured rows', 'The server returns structured rows with value, unit, period and provenance. Errors stay errors, not empty answers.'],
  ['These 237 questions shaped', 'These 237 questions shaped the filters, prompts and limits, so they measure fit, not generalisation.'],
  ['The gold file, prompts, prices', 'The questions and prompts were frozen before the runs, but 25 of 31 share evidence with development.'],
  ['The 65 questions were written blind', 'Sixty-five questions on six new sources, written blind. Once run they became known and are no longer unseen.'],
  ['Official observations are the numerical reference', 'Official data is the numerical reference, with population, unit, adjustment and release kept separate.'],
  ['The gold questions and evidence labels were drafted', 'AI helped draft the questions and labels. One human reviewer signed them off after scoring.'],
  ['The data sheet records 33 dataset licences', 'Of 36 datasets, 33 licences are verified. 23 document rights are still unresolved.'],
  ['Official public sources only', 'Official public sources only. Restricted text and indexes stay local; public material is linked and attributed.'],
  ['Default graph limits: six total', 'Six tool calls over two evidence rounds, one retry and one repair. No SQL, shell or open browsing.'],
  ['Generation candidates share a provider family', 'Models share one provider family and use default sampling. Two runs do not show run-to-run variance.'],
  ['The assessment deadline is 4 November', 'The deadline is 4 November 2026, morning Singapore time. A provider-side spend cap was not verified.'],
  ['The answer boundary is fixed', 'Answers cover Q1 2020 to Q2 2026. Requests that need an earlier period must abstain. Only 2024 to 2026 was evaluated.'],
  ['The current data sheet records 36 statistical', 'The data sheet records 36 datasets and 106 documents. Observations and passages are stored separately with provenance.'],
  ['Keyword, dense and hybrid retrieval were compared', 'Three retrieval methods were compared. The agent uses report search, statistics lookup and exact calculation.'],
  ['Saved evaluation covers development', 'Evaluation covers development, original test and fresh questions, with known failures and rights limits.'],
  ['Unsupported causal attribution', 'Out of scope: causal claims, forecasts, personal employment advice and open web research.'],
  ['Immutable hashed source snapshots', 'Hashed source snapshots become Parquet. The statistics tool reads this validated store, not the report index.'],
  ['Eligible neighbouring passages merge', 'Neighbouring passages merge into chunks of about 200 words. Keyword and meaning search use the same chunks.'],
  ['experiments/scanner/v2-baseline-test/metrics.json', 'The scanner flagged 10 of 30 attacks before and 23 of 30 after, with 9 of 30 false alarms. A warning layer.'],
  ['Fixed minus agent: -7.17', 'The fixed pipeline scored 7.2 points below the agent, interval -12.2 to -2.1, with several confounds. One run.'],
  ['Accuracy in the two runs', 'Runs scored 88.6% and 90.7%, mean 89.7%, on 237 questions. Two runs do not show variance.'],
  ['Development questions, 237 questions.', 'The 237 development questions: 89.7% filtered and reranked against 82.7% hybrid, a paired +7.0 points.'],
  ['Original test, 31 questions.', 'The 31 original test questions: 83.9% against 80.6%, paired +3.2 points. The interval includes zero.'],
  ['claude-sonnet-5-5 re-judged the answers', 'A second judge re-scored 120 sampled answers. Its claim-support sign differed from the first judge.'],
  ['A real case: a numerical comparison', 'A real development case: the question asked about 2023, so declining was right. The new tool gave a false answer.'],
  ['Why it did not work', 'The new tool failed two pre-declared rules and was not adopted. The measurements do not show why.'],
  ['The planner sees the question', 'The planner sees the question and catalogue, then picks from three fixed tools.'],
  ['Worked example: a flattened table', 'A flattened table loses its columns, so each value\u2019s quarter is unclear. A claim fails unless its quote is in the passage.'],
  ['Worked example: a question before the period', 'Asked about 2019-Q4, the agent declines. The supported period is 2020-Q1 to 2026-Q2. An example, not a run.'],
  ['no separate test of sensitive-data refusal', 'There is no separate test of refusing sensitive data. The refusal policy and absence of a personal-data tool apply to both arms.'],
  ['tests/test_security.py: 5 deterministic guard tests pass, covering input flags', 'Five guard tests pass. They check detection, not whether the model resists.'],
  ['No separate test of model obedience', 'There is no separate test of whether the model obeys passage instructions. Passage isolation stayed on.'],
  ['tests/retrieval/test_crosscheck.py', 'Twenty-six cross-check tests pass, yet a planted figure failed again. Tests do not prove end-to-end reliability.'],
  ['Published ratio against the counts, 2024-Q2', 'The published Q2 2024 vacancy ratio is 1.72. Rebuilding it from the two counts gives 1.05, because the surveys differ.'],
  ['tests/retrieval/test_agent.py: 3 tool-boundary', 'Three tool-boundary tests pass: scope, call and round caps, and recovery from bad arguments.'],
  ['tests/mcp/test_mcp.py: 9 boundary checks', 'Nine boundary checks and ten hostile-server cases pass. They test the client boundary, not answer accuracy.'],
  ['No separate test of causal or forecast refusal', 'There is no separate test of refusing causal or forecast requests. The guarded answer prompt sets scope and caveats.'],
  ['tests/retrieval/test_answer_validate.py', 'Six answer-validation tests pass. They check structure, not whether a quote supports its claim.'],
  ['gpt-6-luna, claim support. Filter then rerank minus hybrid', 'Claim support: +2.8 points under one judge, -1.1 under the second. The sign differs, so it is not settled.'],
  ['gpt-6-luna, fact coverage. Filter then rerank minus hybrid', 'Fact coverage: +4.3 points under both judges, on 57 valid pairs.'],
];

const sentencesOf = text => String(text ?? '')
  .split(/\n+/)
  .flatMap(line => line.trim().split(/(?<=[.!?])\s+(?=[A-Z0-9$(])/))
  .map(s => s.trim()).filter(Boolean);
const closed = s => (/[.!?]$/.test(s) ? s : `${s.replace(/[;:,\s]+$/, '')}.`);

/** Cut one over-long sentence at its last clean clause boundary: a semicolon or colon first, then a comma. */
function clause(sentence, limit) {
  const words = wordList(sentence);
  let strong = 0, comma = 0;
  for (let i = 1; i <= Math.min(limit, words.length); i += 1) {
    const w = words[i - 1];
    if (!strong && i >= 7 && /[;:]$/.test(w)) strong = i;
    if (i >= 8 && /,$/.test(w)) comma = i;
  }
  const cut = strong || comma || limit;
  const kept = words.slice(0, cut);
  // With no clause boundary, step back so the text does not end on a function word.
  if (!strong && !comma) while (kept.length > 4 && /^(and|or|the|a|an|of|to|in|on|at|for|with|by|as|that|which|is|are|was|were|from|than|but)$/i.test(kept[kept.length - 1])) kept.pop();
  const out = kept.join(' ');
  return cut >= words.length ? out : closed(out);
}

/** A short, plain version of `text`: at most `limit` words, one idea, ending on a whole clause. Hand-written summaries win. */
export function shorten(text, limit = TIP_WORDS) {
  const source = String(text ?? '').trim();
  const hit = OVERRIDES.find(([start, short]) => short && source.startsWith(start));
  if (hit) return hit[1];
  if (wordCount(source) <= limit) return source.replace(/\n+/g, ' ');
  const parts = sentencesOf(source);
  let out = parts[0] || '';
  if (wordCount(out) > limit) return closed(clause(out, limit));
  // A short opening (a title or label) is not an idea on its own. Add the next sentence when it still fits, and always when the opening is tiny.
  // A modest opening also takes a following sentence that carries the figures.
  for (let i = 1; i < parts.length; i += 1) {
    const next = `${closed(out)} ${parts[i]}`, n = wordCount(out);
    if (!(n < 6 || (n < 12 && /\d/.test(parts[i])))) break;
    if (wordCount(next) > limit) {
      // Only a tiny opening is worth a clause of the next sentence; a modest one stands alone.
      if (n < 6) out = closed(`${closed(out)} ${clause(parts[i], limit - n)}`);
      break;
    }
    out = next;
  }
  return closed(out);
}

/** Every popover original, keyed by its trigger. Read back by `tipNotes` to build the slide's speaker notes. */
const originals = new WeakMap();
export function recordOriginal(node, label, full) {
  const list = originals.get(node) || [];
  if (!list.some(x => x.full === full)) list.push({label, full});
  originals.set(node, list);
}

const tidy = text => String(text ?? '').replace(/\s+/g, ' ').trim();
/** The name of a trigger as a reader would say it: its own text without the popover, or a fallback, in a few words. */
export function triggerLabel(node, fallback = '') {
  const own = tidy([...node.childNodes].filter(n => !n.classList?.contains('deck-tip')).map(n => n.textContent).join(' '));
  const base = own || tidy(fallback) || tidy(node.getAttribute?.('aria-label')?.split(/\.\s/)[0]);
  const w = wordList(base);
  return w.length > 9 ? `${w.slice(0, 9).join(' ')}\u2026` : base;
}

/** Turn popover DOM content (a table or a worked example) into a summary and the full text. */
export function describeContent(content) {
  const table = content.querySelector('table');
  const rows = [...content.querySelectorAll('tbody tr')];
  const paras = [...content.querySelectorAll('p')].map(p => tidy(p.textContent)).filter(Boolean);
  const title = tidy(content.querySelector('.rx-title')?.textContent);
  const note = tidy(content.querySelector('.rx-note')?.textContent);
  const body = table ? rows.map(tr => [...tr.cells].map(c => tidy(c.textContent)).join(', ')) : paras.slice(title ? 1 : 0);
  const full = [title, ...body, table && note && !body.includes(note) ? note : ''].filter(Boolean).map(closed).join(' ');
  const short = table ? `${title || 'Dataset rows'}: ${rows.length} row${rows.length === 1 ? '' : 's'} with value, unit, release stage and date.` : shorten(paras.join('\n'));
  return {short, full};
}

/** Short and full text for a popover whose content is a string or DOM node. */
export function summarise(content) {
  if (typeof content === 'string') return {short: shorten(content), full: content.replace(/\s*\n+\s*/g, ' ')};
  return describeContent(content);
}

/** Classes that size a popover for a table or paragraph are dropped once the text is short. */
export const shortClass = cls => cls.split(/\s+/).filter(c => c && c !== 'is-table' && c !== 'is-wide').join(' ');

/** Lines of a chart point's popover, cut by whole rows (never mid-row) until they fit. A heading and its first figure row always stay,
 *  up to the hard limit. The original lines are recorded on the node. */
export function chartLines(lines, node) {
  const all = lines.map(tidy).filter(Boolean);
  if (wordCount(all.join(' ')) <= TIP_WORDS) return lines;
  const kept = [all[0]];
  for (const line of all.slice(1)) { if (wordCount([...kept, line].join(' ')) > (kept.length < 2 ? TIP_MAX : TIP_WORDS)) break; kept.push(line); }
  if (kept.length === all.length) return lines;
  recordOriginal(node, all[0], all.map(closed).join(' '));
  return kept;
}

const held = (node, text) => (originals.get(node) || []).some(x => text.includes(x.full) || x.full.includes(text))
  || tidy(node.querySelector?.(':scope > .deck-tip')?.textContent) === text;
/** Native titles and long spoken labels. A native title on a node that already has a popover is a duplicate and is removed; a title or
 *  aria-label elsewhere is cut to the same size. Whatever was longer goes to the notes unless the popover original already holds it. */
export function tightenLabels(root) {
  root.querySelectorAll('[title]').forEach(node => {
    const text = tidy(node.getAttribute('title'));
    const tipped = node.classList.contains('has-tip') || node.classList.contains('is-tipped');
    if (!tipped && wordCount(text) <= TIP_MAX) return;
    if (wordCount(text) > TIP_MAX || tipped) { if (!held(node, text)) recordOriginal(node, '', text); }
    if (tipped) node.removeAttribute('title'); else node.setAttribute('title', shorten(text));
  });
  root.querySelectorAll('svg title').forEach(title => {
    const text = tidy(title.textContent), owner = title.parentElement;
    const tipped = owner.classList.contains('is-tipped');
    if (!tipped && wordCount(text) <= TIP_MAX) return;
    if (!held(owner, text)) recordOriginal(owner, '', text);
    if (tipped) title.remove(); else title.textContent = shorten(text);
  });
  root.querySelectorAll('[aria-label]').forEach(node => {
    const label = tidy(node.getAttribute('aria-label'));
    if (wordCount(label) <= TIP_MAX) return;
    if (!held(node, label)) recordOriginal(node, '', label);
    node.setAttribute('aria-label', shorten(label));
  });
}

/** One speaker-note line per shortened popover, title or label inside `root`. The notes keep the original wording. */
export function tipNotes(root) {
  const lines = [];
  root.querySelectorAll('*').forEach(node => {
    (originals.get(node) || []).forEach(({label, full}) => {
      if (lines.some(l => l.endsWith(`: ${full}`))) return;
      lines.push(`Popover detail, ${triggerLabel(node, label) || 'item'}: ${full}`);
    });
  });
  return lines;
}
