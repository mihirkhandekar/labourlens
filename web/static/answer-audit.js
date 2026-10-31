const FEEDBACK_TAGS = [
  ['wrong_number', 'Wrong number'],
  ['wrong_source', 'Wrong source'],
  ['missing_info', 'Missing information'],
  ['other', 'Other']
];

const element = (tag, className, text) => {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
};

const label = key => key
  .replace(/([a-z0-9])([A-Z])/g, '$1 $2')
  .replace(/[_-]+/g, ' ')
  .replace(/^./, character => character.toUpperCase());

/** Show only the server's valid audit identifier, never arbitrary response text. */
export function decorateAnswer(target, response) {
  const runId = response?.run_id ?? response?.answer?.run_id;
  if (typeof runId === 'string' && /^[a-f0-9]{12}$/.test(runId)) {
    target.append(element('p', 'audit-id mono', `Audit ID ${runId}`));
  }
  return target;
}

/** Data-quality notes are deterministic trace details, not citeable evidence. */
export function dataNotes(response) {
  const trace = Array.isArray(response?.trace) ? response.trace : response?.trace?.events;
  if (!Array.isArray(trace)) return [];
  return trace.flatMap(event => {
    if (event?.node !== 'assess_evidence') return [];
    const notes = event.detail?.data_quality_notes;
    return Array.isArray(notes) ? notes : [];
  });
}

function renderNote(value) {
  if (Array.isArray(value)) {
    const list = element('ul', 'detail-list');
    value.forEach(item => {
      const row = element('li');
      row.append(renderNote(item));
      list.append(row);
    });
    return list;
  }
  if (value !== null && typeof value === 'object') {
    const fields = element('dl', 'evidence-fields');
    Object.entries(value).forEach(([key, item]) => {
      const detail = element('dd');
      detail.append(renderNote(item));
      fields.append(element('dt', '', label(key)), detail);
    });
    return fields;
  }
  const text = value === null || value === undefined
    ? 'Not recorded'
    : typeof value === 'boolean' ? (value ? 'Yes' : 'No') : String(value);
  return element('span', '', text);
}

/** Render nested notes as human-readable text and labelled fields, never JSON/HTML. */
export function renderDataNotes(parent, notes) {
  if (!Array.isArray(notes) || notes.length === 0) return parent;
  const section = element('section', 'data-notes');
  section.append(
    element('h3', '', 'Data notes'),
    element('p', 'small muted', 'Data-quality notes from the evidence tools. They are not citations.'),
    renderNote(notes)
  );
  parent.append(section);
  return parent;
}

/** Each label wraps its input so multiple answer forms need no shared DOM IDs. */
export function feedbackTags() {
  const fieldset = element('fieldset', 'feedback-tags');
  fieldset.append(element('legend', '', 'Issue type (optional)'));
  FEEDBACK_TAGS.forEach(([value, text]) => {
    const option = element('label');
    const input = element('input');
    input.type = 'checkbox';
    input.name = 'feedback_tag';
    input.value = value;
    option.append(input, element('span', '', text));
    fieldset.append(option);
  });
  return fieldset;
}

export function selectedTags(form) {
  const checked = new Set(Array.from(
    form.querySelectorAll('input[name="feedback_tag"]:checked'),
    input => input.value
  ));
  return FEEDBACK_TAGS.filter(([value]) => checked.has(value)).map(([value]) => value);
}
