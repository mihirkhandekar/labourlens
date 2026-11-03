import {el, fmt} from '../charts.js';
import {chapter, section, callout, evi, dataTable, textStat, list} from './ui.js';
import {contextSentence} from './model.js';

// What the live web app adds to the system the experiments measured. Numbers come from report.json
// (serving, mcp); the wording of each difference is from the decision log, named in the evidence line.

const usd = value => (Number.isFinite(value) ? `$${value.toFixed(4)}` : 'not recorded');
const secs = value => (Number.isFinite(value) ? `${value.toFixed(2)} s` : 'not recorded');
const of = (part, whole) => (Number.isFinite(part) && Number.isFinite(whole) ? `${fmt.int(part)} of ${fmt.int(whole)}` : 'not recorded');

function differenceCards(m) {
  const sv = m.section('serving'), t = sv.triage || {}, corpus = sv.corpus || {};
  const mcp = m.section('mcp'), mx = mcp.metrics || {};
  const lat = (mcp.rows || []).find(r => r.metric === 'latency_p50_ms') || {};
  const cl = t.cost_and_latency || {};
  const cards = [
    ['Small-talk reply', `Greetings, thanks, "help", "who are you" and messages with no letters or digits are answered from a fixed list: no model call, no search, no cost. The whole message must match, so "hi, ignore previous instructions" and "what can you do about unemployment" still go to the agent. Phrasings off the list run the whole agent. Unit-tested; included in the separate 65-case served-chain sample.`, 'docs/decisions.md › D-050 · tests/web/test_smalltalk.py'],
    ['Scope check before the agent', `One short model call decides whether a message is about the workbench's subject. Off-topic, personal-advice and unsafe messages get a brief refusal; when unsure it defaults to in scope; if the call fails the agent runs anyway. It adds one call to each question that is not small talk${cl.mean_cost_usd != null ? `, about ${usd(cl.mean_cost_usd)} and ${secs(cl.latency_p50_s)} at the median` : ''}. Measured end to end on a separate 65-case sample, not the full final sets.`, 'docs/decisions.md › D-051 · tests/web/test_triage.py'],
    ['Follow-up rewrite before the agent', `When a message follows earlier turns or uses a relative date such as last quarter, one short model call turns it into a standalone question first. A first question with no such wording passes through with no call, and if the call fails the original question goes to the agent. ${contextSentence(sv)}`, 'docs/decisions.md › D-054 · experiments/context/ctx-v1-luna, ctx-v2-luna'],
    ['Statistics lookups through MCP', `The agent's get_series tool calls the local MCP server over stdio, and the workbench activity shows "via MCP". Report search and the change calculation stay in the same process, and the other eight MCP tools are not given to the agent. ${lat.mcp != null ? `Median ${lat.mcp} ms per call against ${lat.direct} ms direct` : 'Latency per call is not recorded'}${mx.connection_seconds != null ? `, and about ${mx.connection_seconds.toFixed(1)} s once to connect` : ''}. The 65-case served-chain sample (51 development cases and 14 probes, statistics-only MCP; not the fresh 65) scored 90.8% for both models, with no observed loss versus direct calls.`, 'docs/decisions.md › D-053 · docs/mcp-demo-transcript.md §17'],
    ['Document build v4', `${corpus.sources != null ? `${fmt.int(corpus.sources)} sources, ${fmt.int(corpus.passages)} passages and ${fmt.int(corpus.chunks)} chunks, parser ${corpus.parser_after || 'not recorded'}.` : 'Corpus counts are not recorded.'} Build v4 adds the 2020 to 2022 quarterly reports and the 2020 to 2023 annual reports to v3.1; passage ids of the earlier documents are unchanged, and no evaluation ran on v4. The final evaluation of all three question sets ran on v3.1 and gives the headline numbers. Earlier results ran on earlier builds and stay as labelled history.`, 'docs/decisions.md › D-052, D-055 · experiments/corpus-snapshots/v4.json']
  ];
  const grid = el('div', 'pr-limit-grid');
  cards.forEach(([title, text, src], i) => {
    const card = el('article', 'pr-limit');
    card.append(el('span', 'pr-limit-no', String(i + 1).padStart(2, '0')), el('h5', 'pr-limit-title', title), el('p', '', text), evi(src));
    grid.append(card);
  });
  return grid;
}

function triageBlock(m) {
  const sv = m.section('serving'), t = sv.triage || {};
  const g = t.gold_and_fresh || {}, th = t.threats || {}, off = t.offtopic || {}, cl = t.cost_and_latency || {};
  const kinds = Object.fromEntries((sv.rows || []).map(r => [r.kind, r]));
  const bl = ['borderline_inscope', 'borderline_offtopic'].map(k => kinds[k]).filter(Boolean);
  const blN = bl.reduce((a, r) => a + r.n, 0), blOk = bl.reduce((a, r) => a + r.correct, 0);
  const block = section(`Scope check measured alone: ${of(g.false_out_of_scope, g.n)} reference and fresh questions wrongly turned away`, ['One call per question, one run, 409 calls in all.', 'Measured on its own: the agent did not run, so no end-to-end result exists.']);
  const stats = el('div', 'pr-stats');
  stats.append(
    textStat({text: of(g.false_out_of_scope, g.n), label: 'Reference and fresh questions turned away', note: 'None failed open', src: 'report.json › serving.triage.gold_and_fresh'}),
    textStat({text: of(th.false_out_of_scope, th.n), label: 'Threat cases turned away', note: 'A request to decode a base64 string, politely declined before the agent: safe, but a different route from the one evaluated', tone: 'brass', src: 'report.json › serving.triage.threats'}),
    textStat({text: of(off.recall_not_in_scope, off.expected_not_in_scope), label: 'Off-topic messages caught', note: 'Hand-written: general knowledge, creative, coding, medical, legal, personal advice, chit-chat', src: 'report.json › serving.triage.offtopic'}),
    textStat({text: of(blOk, blN), label: 'Borderline messages routed correctly', note: '10 that mention Singapore or jobs but are off topic, 10 that are in scope', src: 'report.json › serving.rows'}),
    textStat({text: usd(cl.total_cost_usd), label: `Cost of ${fmt.int(cl.calls)} calls`, note: 'List price, gpt-6-luna', src: 'report.json › serving.triage.cost_and_latency'}),
    textStat({text: `${secs(cl.latency_p50_s)} / ${secs(cl.latency_p95_s)}`, label: 'Latency, median / 95th percentile', note: 'Added to every question that is not small talk', src: 'report.json › serving.triage.cost_and_latency'})
  );
  block.append(stats);
  const names = {clear_offtopic: 'Clearly off topic', borderline_offtopic: 'Borderline, off topic', borderline_inscope: 'Borderline, in scope', clear_small_talk: 'Small talk', clear_unsafe: 'Unsafe or sensitive'};
  block.append(dataTable('Hand-written messages by kind', ['Kind', 'Messages', 'Routed correctly'], Object.keys(names).filter(k => kinds[k]).map(k => [names[k], fmt.int(kinds[k].n), fmt.int(kinds[k].correct)])));
  block.append(evi('experiments/triage/triage-v1-luna/metrics.json · report.json › serving.rows'));
  return block;
}

function corpusBlock(m) {
  const c = m.section('serving').corpus;
  if (!c) return null;
  const f = c.quality_flags || {}, tr = c.flag_transitions || {};
  const ev = m.section('serving').evaluated_corpus || {};
  const block = section(`Evaluated document build v3.1: ${fmt.int(ev.passages)} passages, ${fmt.int(ev.chunks)} chunks, parser ${c.parser_after}`, ['No passage was added or removed; the changes are labels on one article.', 'The parser version field changes on every passage record.']);
  block.append(dataTable('Passage quality flags, build v3 against build v3.1', ['Measure', 'v3', 'v3.1'], [
    ['Passages in the corpus', fmt.int(ev.passages), fmt.int(ev.passages)],
    ['Garbled, whole corpus', fmt.int(f.all_before?.garbled), fmt.int(f.all_after?.garbled)],
    ['Usable text, whole corpus', fmt.int(f.all_before?.ok), fmt.int(f.all_after?.ok)],
    ['Table fragments kept but not retrieved, whole corpus', fmt.int(f.all_before?.table_unreliable), fmt.int(f.all_after?.table_unreliable)],
    ['Garbled, MTI feature article', fmt.int(f.mti_before?.garbled), fmt.int(f.mti_after?.garbled ?? 0)],
    ['Chunk ids replaced, all in the MTI feature article', `${fmt.int(c.chunks_changed?.ids_removed)} removed`, `${fmt.int(c.chunks_changed?.ids_added)} added`]
  ]));
  block.append(el('p', 'pr-block-intro', `Of the 40 garbled passages in the article, ${fmt.int(tr.garbled_to_ok)} became usable text and ${fmt.int(tr.garbled_to_table_unreliable)} became table fragments; ${fmt.int(tr.ok_to_table_unreliable)} usable passages became table fragments. ${fmt.int(f.new_garbled ?? 0)} passages became garbled. ${fmt.int(c.embeddings?.unique_inputs_missing_from_cache_after)} chunk texts need new embedding vectors.`));
  block.append(evi('report.json › serving.corpus · experiments/corpus-snapshots/v3.1-diff.json'));
  return block;
}

export function knownLimits(m) {
  const r = m.section('serving').rights || {};
  return [
    'The reference labels began as AI drafts. One reviewer signed off every item after three AI review passes and after the runs were scored. These are agreement figures, not validated accuracy, and not independent inter-rater evidence.',
    'The judge and the answer models come from one provider family, so their errors may correlate.',
    'The final comparisons use two runs per arm; this is not a run-to-run variance estimate. Other experiments have one run unless labelled otherwise.',
    'Temperature and reasoning effort were not varied. New runs record provider-default temperature and top_p, no seed, prompt hashes and completion limits; older runs lack that sampling block.',
    'The scanner flags 23/30 test attacks after improvement, with 9/30 benign false alarms and 0/15 on real report passages. Semantic and non-English bypasses remain; zero flags never establishes source safety.',
    'A provider-side spend cap is not verified; the app\u2019s own daily budget is an estimate.',
    r.datasets_unverified != null ? `Licences are unverified for ${fmt.int(r.datasets_unverified)} datasets (assumed open) and ${fmt.int(r.sources_unresolved)} documents (rights unresolved). All of them stay local and none is committed.` : 'Licence status is not recorded.',
    'The live app differs from the evaluated system (small-talk reply, scope check, MCP route, build v4 against v3.1), and a separate 65-case sample measures the served configuration, not the full final sets.'
  ];
}

export function renderServing(m, ctx) {
  const sv = m.section('serving');
  const t = sv.triage || {}, g = t.gold_and_fresh || {};
  const ch = chapter({
    id: 'serving',
    title: 'The live app differs from the system I evaluated in four ways',
    bullets: [
      'A small-talk reply, a scope check, statistics lookups through MCP and document build v4, which was not evaluated.',
      g.n != null ? `The scope check alone measured: ${of(g.false_out_of_scope, g.n)} reference and fresh questions wrongly turned away. The served chain also has a 65-case sample (51 development cases and 14 probes, statistics-only MCP; not the fresh 65), 90.8% for both models.` : 'The served chain also has a 65-case sample (51 development cases and 14 probes, statistics-only MCP; not the fresh 65), 90.8% for both models.',
      'The served sample contains 51 development cases and 14 hand-written probes, one run, same judge family, not independent evidence.'
    ]
  });
  const a = section('Four differences between the live app and the evaluated system');
  a.append(differenceCards(m));
  ch.body.append(a);
  if (sv.triage) ch.body.append(triageBlock(m));
  const corpus = corpusBlock(m);
  if (corpus) ch.body.append(corpus);
  const lim = section('Known limits of the evidence');
  lim.append(list(knownLimits(m)));
  lim.append(evi('docs/evaluation-report.md › Read this first · docs/data-sheet.md · docs/deploy.md'));
  ch.body.append(lim);
  ch.body.append(callout({tone: 'warn', title: 'Reading the scope-check numbers', text: 'Small hand-written sets, one run, the same model family. Borderline messages depend on the model\u2019s judgement. This is not a general guarantee that real questions are never turned away.', src: 'docs/decisions.md › D-051'}));
  return ch.root;
}
