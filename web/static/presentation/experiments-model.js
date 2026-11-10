// One normalised list of experiment cards, shared by the deck page (experiments.js) and the generated report page
// (scripts/build_experiment_notebook.mjs), so the two cannot drift. No DOM access here.
import data from './experiments-data.js';
import {EXPERIMENTS_B} from './experiments-data-b.js';
import {NOTES} from './experiments-notes.js';

export const GROUPS = [['retrieval', 'Retrieval'], ['generation', 'Generation'], ['agent', 'Agent'], ['threat', 'Threat']];
export const DEFINITIONS = data.definitions;

const extra = EXPERIMENTS_B.map(item => ({
  ...item,
  changed: item.factorsChanged.join(' '),
  fixed: item.heldFixed.join(' '),
  measurement: `${item.measurement.cases}; n=${item.measurement.n}. Build: ${item.measurement.corpusOrSystem}. ${item.measurement.metrics.join(' ')}`,
  tables: [...(item.table ? [item.table] : []), ...(item.tables || [])].map(t => ({...t, title: t.caption})),
  exampleNote: `${item.example.title}: ${item.example.lines.join(' ')}`,
  examples: [],
  limit: item.doesNotShow
}));

export function allExperiments() {
  return [...data.experiments, ...extra].map(card => {
    const note = NOTES[card.id];
    if (!note) throw new Error(`experiments-notes.js has no entry for card ${card.id}`);
    return {...card, calculated: note.calculated, decision: note.decision};
  });
}
