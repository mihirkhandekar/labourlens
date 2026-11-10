// Writes docs/experiments/experiment-notebook.md from the same card data the deck's E-E page renders
// (web/static/presentation/experiments-model.js), so the report and the deck cannot disagree.
// Usage: node scripts/build_experiment_notebook.mjs [--check]
// --check exits 1 when the committed page is out of date instead of writing it.
import {readFileSync, writeFileSync, existsSync} from 'node:fs';
import {fileURLToPath, pathToFileURL} from 'node:url';
import {dirname, join} from 'node:path';

const root = join(dirname(fileURLToPath(import.meta.url)), '..');
const deck = join(root, 'web/static/presentation');
const {GROUPS, DEFINITIONS, allExperiments} = await import(pathToFileURL(join(deck, 'experiments-model.js')));
const {GLOSSARY, termsIn} = await import(pathToFileURL(join(deck, 'experiments-glossary.js')));
const out = join(root, 'docs/experiments/experiment-notebook.md');

const cell = value => String(value ?? '-').replace(/\|/g, '\\|').replace(/\s*\n\s*/g, ' ');
function table(spec) {
  const lines = [`**${spec.title || 'Measured results'}**`, '', `| ${spec.columns.map(cell).join(' | ')} |`, `|${spec.columns.map(() => '---').join('|')}|`];
  for (const row of spec.rows) lines.push(`| ${row.map(cell).join(' | ')} |`);
  lines.push('', `Source: \`${spec.source}\``, '');
  return lines.join('\n');
}
// GitHub-style heading anchors (the same rule scripts/check_docs.py applies).
const seen = new Map();
const slug = title => {
  const base = title.replace(/[`*_]|<[^>]+>/g, '').trim().toLowerCase().replace(/[^\p{L}\p{N}_\- ]/gu, '').replaceAll(' ', '-');
  const n = seen.get(base) ?? 0;
  seen.set(base, n + 1);
  return n === 0 ? base : `${base}-${n}`;
};
const experiments = allExperiments();
const anchors = new Map(experiments.map(e => [e.id, slug(e.title)]));
const parts = [];
parts.push(`# Experiment notebook

Every saved experiment in one place: retrieval, answer generation, the agent, and threat tests. This page is generated from the same data as the deck's experiment notebook (press **E** twice in the deck), by \`node scripts/build_experiment_notebook.mjs\`. Do not edit it by hand.

Each card reads in the same order: **what we wanted to know**, **what we changed**, **what stayed fixed**, **what we calculated**, **how it was measured**, the **result**, **what we found**, **what we chose**, and **what this does not show**. Results belong to the build named on each card, which is not necessarily the live application. Numbers are copied from the cited saved artefacts; no report passage text is reproduced. Figures for the secondary final-system model appear only in the [evaluation report](../evaluation-report.md) and its [detail](../reference/evaluation-detail.md).

## How to read the measurements

${DEFINITIONS}

## What the labels mean
`);
let last = '';
for (const {group, term, text} of GLOSSARY) {
  if (group !== last) { parts.push(`\n**${group}**\n`); last = group; }
  parts.push(`- **${term}**: ${text}`);
}
parts.push(`\n## Index\n\n| Id | Card | What we chose |\n|---|---|---|`);
for (const e of experiments) parts.push(`| ${cell(e.id)} | [${cell(e.title)}](#${anchors.get(e.id)}) | ${cell(e.decision)} |`);
for (const [group, label] of GROUPS) {
  parts.push(`\n## ${label}\n`);
  for (const e of experiments.filter(card => card.group === group)) {
    parts.push(`### ${e.title}\n`);
    parts.push(`- **What we wanted to know:** ${e.question}`);
    parts.push(`- **What we changed:** ${e.changed}`);
    parts.push(`- **What stayed fixed:** ${e.fixed}`);
    parts.push(`- **What we calculated:** ${e.calculated}`);
    parts.push(`- **How it was measured:** ${e.measurement}\n`);
    const terms = termsIn(JSON.stringify(e));
    if (terms.length) parts.push(`*Labels on this card:* ${terms.map(t => `**${t.term}**: ${t.text}`).join(' ')}\n`);
    for (const spec of e.tables) parts.push(table(spec));
    for (const ex of e.examples) {
      parts.push(table({title: `${ex.case_id} · ${ex.label}: saved ranked candidates (first relevant rank: ${ex.first_relevant_rank ?? 'not in saved ranking'})`, source: ex.source,
        columns: ['Rank', 'Chunk id', 'Relevant', 'Score', 'Words', 'Source id', 'Locator'], rows: ex.ranked.map((r, i) => [i + 1, r.chunk_id, r.relevant, r.score, r.words, r.source_id, r.locator])}));
    }
    parts.push(`**What we found:** ${e.takeaway}\n`);
    parts.push(`**What we chose:** ${e.decision}\n`);
    parts.push(`**What this does not show:** ${e.limit}\n`);
    parts.push(`**Worked example.** ${e.exampleNote}\n`);
  }
}
const text = `${parts.join('\n').replace(/\n{3,}/g, '\n\n').trimEnd()}\n`;
if (process.argv.includes('--check')) {
  if (!existsSync(out) || readFileSync(out, 'utf8') !== text) { console.error('docs/experiments/experiment-notebook.md is out of date; run: node scripts/build_experiment_notebook.mjs'); process.exit(1); }
  console.log('experiment notebook page is up to date');
} else {
  writeFileSync(out, text);
  console.log(`wrote ${out} (${experiments.length} cards)`);
}
