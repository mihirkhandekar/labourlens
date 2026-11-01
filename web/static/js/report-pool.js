// The presentation's chapter modules draw every chart and table from report.json. The report renders
// each chapter once, off screen, then picks figures out by id and puts what is left into the details
// under the matching band, so no experiment table is lost.
import {el} from './dom.js';
import {model} from '../presentation/model.js';
import {renderScope} from '../presentation/ch1-scope.js';
import {renderData} from '../presentation/ch2-data.js';
import {renderRetrieval} from '../presentation/ch3-retrieval.js';
import {renderAgent} from '../presentation/ch4-agent.js';
import {renderEvaluation} from '../presentation/ch5-evaluation.js';
import {renderSafety} from '../presentation/ch6-safety.js';
import {renderMcp} from '../presentation/ch7-mcp.js';
import {renderServing} from '../presentation/ch-serving.js';
import {renderLimits, renderNext, renderSummary} from '../presentation/ch8-limits.js';
import {renderWork} from '../presentation/ch-work.js';
import {evaluationNotices} from '../evaluation.js';

const CHAPTERS = {scope: renderScope, data: renderData, retrieval: renderRetrieval, agent: renderAgent, evaluation: renderEvaluation, safety: renderSafety, mcp: renderMcp, serving: renderServing, limits: renderLimits, next: renderNext, work: renderWork, summary: renderSummary};

export function buildPool(report) {
  const m = model(report);
  const ctx = {disclosures: evaluationNotices(report)};
  const roots = {};
  for (const [key, render] of Object.entries(CHAPTERS)) {
    try { roots[key] = render(m, ctx); } catch (error) {
      console.error(`report chapter ${key}`, error);
      roots[key] = el('section');
    }
  }
  const claimed = new Set();
  const pool = {
    m,
    /** A figure by id, removed from its chapter. Null when the chapter could not draw it. */
    fig(id) {
      for (const root of Object.values(roots)) {
        const node = root.querySelector(`#${id}`);
        if (node) { node.remove(); claimed.add(id); return node; }
      }
      return null;
    },
    /** The first element matching a selector inside one chapter, removed from it. */
    take(key, selector) {
      const node = roots[key]?.querySelector(selector) || null;
      node?.remove();
      return node;
    },
    takeAll(key, selector) {
      return [...(roots[key]?.querySelectorAll(selector) || [])].map(node => { node.remove(); return node; });
    },
    /** What is left of a chapter: its body, without the chapter heading and bullets. Null when empty. */
    rest(key) {
      const body = roots[key]?.querySelector('.pr-chapter-body');
      if (!body || !body.children.length) return null;
      body.classList.add('rp-chapter-rest');
      return body;
    },
    block(key, pattern) {
      const blocks = [...(roots[key]?.querySelectorAll('.pr-block') || [])];
      const node = blocks.find(b => pattern.test(b.querySelector('.pr-block-title')?.textContent || ''));
      node?.remove();
      return node || null;
    }
  };
  return pool;
}
