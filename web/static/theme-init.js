// Runs before first paint: restores the saved theme and marks the page as script-enabled.
(() => {
  const root = document.documentElement;
  root.classList.add('js');
  try {
    const saved = localStorage.getItem('labourlens-theme');
    if (saved === 'light' || saved === 'dark') root.dataset.theme = saved;
  } catch { /* storage blocked: follow the system setting */ }
})();
