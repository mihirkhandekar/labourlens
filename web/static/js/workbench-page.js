// Standalone research workbench. Answers stay in this page's memory only.
import {el} from './dom.js';
import {mountWorkbench} from './workbench.js';

const app = document.querySelector('#app');
const main = el('main', 'view-workbench standalone-workbench');
main.id = 'main';
main.tabIndex = -1;
app.replaceChildren(main);

const bench = mountWorkbench(main);
const initial = new URLSearchParams(location.search).get('question');
if (initial) {
  bench.prefill(initial.slice(0, 1000));
  history.replaceState(null, '', location.pathname);
}

document.addEventListener('keydown', event => {
  if (event.target.closest('input,textarea,select,button,a') || event.ctrlKey || event.metaKey || event.altKey || bench.isDrawerOpen()) return;
  if (event.key === '/') { event.preventDefault(); bench.focusComposer(); }
});
