"""Closed-grammar cross-check of passage figures against validated observations.

Never infer a population/adjustment or compare a change with a level. Unrecognised
prose is unchecked, not certified. Release reconciliation remains authoritative.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from decimal import Decimal

from labourlens.answer.schema import Answer, Citation, Claim
from labourlens.data.reconcile import QUARTERS
from labourlens.retrieval.period import parse

_NUMBER = r"(?P<value>\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+(?:\.\d+)?)"
# Explicit level statements only: do not turn percentage-point changes into rates.
_LEVEL = re.compile(r"\b(?:was|were|stood at|totalled|totaled|recorded|of|at)\s+" + _NUMBER + r"\s*(?P<unit>%|per cent|percent|persons|employees|workers|vacancies|jobs|ratio)\b", re.I)
_PERCENT = re.compile(r"\b(?:was|were|stood at|of|at)\s+" + _NUMBER + r"\s*(?P<unit>%)", re.I)

_ALIASES = {
    'job_vacancy_rate': r'\bjob vacancy rate\b',
    'job_vacancy_count': r'\b(?:number of job vacancies|job vacancies)\b',
    'vacancy_to_unemployed_ratio': r'\b(?:job vacancy to unemployed person ratio|vacancy.to.unemployed ratio)\b',
    'reentry_6m': r'\bre.entry\b.{0,60}\b6 months\b',
    'reentry_12m': r'\bre.entry\b.{0,60}\b12 months\b',
    'resignation_rate': r'\b(?:average monthly )?resignation rate\b',
    'recruitment_rate': r'\b(?:average monthly )?recruitment rate\b',
    'unemployed_residents': r'\b(?:number of unemployed residents|unemployed residents)\b',
    'unemployed_overall': r'\b(?:number of overall unemployed|overall unemployed)\b',
}

@dataclass(frozen=True)
class Figure:
    source_id: str
    period: str
    unit: str
    value: Decimal
    token: str
    adjustment: str | None = None


def figures(text: str) -> list[Figure]:
    out = []
    # A sentence must name exactly one quarter. Decimal points are not boundaries.
    for sentence in re.split(r"(?<=[.!?])\s+(?=[A-Z])|[;\n]", text):
        hints = parse(sentence)
        if len(hints.quarters) != 1:
            continue
        low = sentence.casefold()
        if re.search(r"percentage\s*points?|\bp\.?p\.?\b|\b(?:rose|fell|change|increase|decrease)\b", low):
            continue
        sid, adj = None, None
        if re.search(r"\bretrenchments?\b|\bretrenched\b", low) and not re.search(r"\b(?:industry|sector|manufacturing|services|construction|resident|citizen|permanent|contract)\b", low):
            sid = "retrenched_employees"
        elif "unemployment rate" in low:
            populations = [p for p in ("resident", "overall", "citizen") if re.search(rf"\b{p}s?\b", low)]
            if len(populations) == 1:
                sid = f"{populations[0]}_unemployment_rate"
                adj = "not_adjusted" if "not seasonally adjusted" in low or "unadjusted" in low else "seasonally_adjusted" if "seasonally adjusted" in low else None
                if adj is None:
                    continue
        if sid is None:
            candidates = [key for key, pattern in _ALIASES.items() if re.search(pattern, low)]
            if len(candidates) != 1:
                continue
            sid = candidates[0]
        matches = list(_LEVEL.finditer(sentence)) or list(_PERCENT.finditer(sentence))
        if len(matches) != 1:
            continue
        m = matches[0]
        unit = "percent" if m['unit'].lower() in ("%", "per cent", "percent") else "ratio" if m['unit'].lower() == "ratio" else "persons"
        expected = "ratio" if sid == 'vacancy_to_unemployed_ratio' else "percent" if sid.endswith('_rate') or sid.startswith('reentry_') else "persons"
        if unit != expected:
            continue
        year, quarter = next(iter(hints.quarters))
        out.append(Figure(sid, f"{year}-Q{quarter}", unit, Decimal(m['value'].replace(',', '')), m['value'], adj))
    return out


def agrees(figure: Figure, value: float) -> bool:
    # Half of the reported last decimal place; persons have integral precision.
    precision = Decimal(1).scaleb(figure.value.as_tuple().exponent)
    return abs(figure.value - Decimal(str(value))) <= precision / 2


def annotate(tools, answer: Answer | None = None) -> list[dict]:
    """Add trusted local observations, not backend/model assertions, to evidence.

    Preliminary releases keep their own vintage. Employment-change comparisons
    are deliberately left to QUARTERS reconciliation: their population bases
    differ, so a dataset total must not overwrite a headline release number.
    """
    conflicts = []
    for passage in list(tools.items):
        if not passage.label.startswith('P') or passage.flags:
            continue
        if passage.stage in ('advance', 'preliminary') or 'prelim' in passage.stage:
            continue
        # Existing reconciliation explicitly separates employment headline and
        # dataset definitions for these releases; do not compare their totals.
        if 'total employment' in passage.text.casefold() and 'retrench' not in passage.text.casefold():
            if any(passage.source_id in sources for sources in QUARTERS.values()):
                continue
        candidates = figures(passage.text)
        if answer is not None:
            passage_values = {Decimal(n.replace(',', '')) for n in re.findall(r"\d[\d,]*(?:\.\d+)?", passage.text)}
            for claim in answer.claims:
                if any(c.label == passage.label for c in claim.citations):
                    candidates.extend(f for f in figures(claim.text) if f.value in passage_values and f not in candidates)
        for figure in candidates:
            rows, error = tools.sh.stats.query(figure.source_id, figure.period, figure.period,
                                               adjustment=figure.adjustment)
            if error or len(rows) != 1:
                continue  # ambiguous dimensions/series are not guessed
            row = rows[0]
            if row['dimension'] or row['release_stage'] in ('advance', 'preliminary'):
                continue
            if row['value'] is None or row['unit'] != figure.unit or agrees(figure, row['value']):
                continue
            # Use the same evidence registration/rendering as get_series, but
            # bypass any remote/MCP replacement for the trusted comparison.
            text = (f"{row['title']} | {row['indicator_id']} | {row['dimension'] or 'all'} | {row['period']} | "
                    f"{row['population']}, {row['adjustment']} | {row['display']} | release stage: {row['release_stage']}")
            observation = tools._add('O', row['observation_id'], row['source_id'], row['title'], None,
                                     row['release_stage'], f"observation {row['observation_id']}", text)
            if observation is None:
                observation = next(i for i in tools.items if i.passage_id == row['observation_id'])
            conflict = dict(passage=passage.label, observation=observation.label,
                            series=figure.source_id, period=figure.period, planted=figure.token,
                            value=row['display'])
            if conflict not in conflicts:
                conflicts.append(conflict)
                tools._note(f"Source conflict: {passage.label} disagrees with validated {observation.label} for {figure.source_id}, {figure.period}. Prefer {observation.label} ({row['display']}); disclose the disagreement with both citations.")
    return conflicts


def enforce(answer: Answer, items, conflicts: list[dict]) -> Answer:
    """Deterministically repair used conflicting levels, preserving both sources.

    This is not a model repair/retry. A numeric assertion supported only by the
    disagreeing passage cannot survive even if the model ignores the note.
    """
    if answer.status != 'answered':
        return answer
    answer = answer.model_copy(deep=True)
    by_label = {p.label: p for p in items}
    for conflict in conflicts:
        used = [c for c in answer.claims if any(cit.label == conflict['passage'] for cit in c.citations)]
        if not used:
            continue
        for claim in used:
            # Replace the conflicting claim, not arbitrary numbers elsewhere.
            if any(Decimal(n.replace(',', '')) == Decimal(conflict['planted'].replace(',', ''))
                   for n in re.findall(r"\d[\d,]*(?:\.\d+)?", claim.text)):
                claim.text = f"{conflict['series']} in {conflict['period']}: {conflict['value']} (validated dataset; source conflict)."
                claim.citations = [Citation(label=conflict['observation'], quote=conflict['value']),
                                   Citation(label=conflict['passage'], quote=by_label[conflict['passage']].text.split()[0])]
                # Summary is regenerated from the now-grounded claims rather
                # than global number replacement that could corrupt periods.
                answer.summary = ' '.join(c.text for c in answer.claims)
        note = (f"Source conflict: passage [{conflict['passage']}] disagrees with the validated dataset "
                f"[{conflict['observation']}] for {conflict['series']} in {conflict['period']}; "
                f"the dataset value, {conflict['value']}, is preferred.")
        if note not in answer.caveats:
            answer.caveats.append(note)
        if not any(any(c.label == conflict['observation'] for c in claim.citations) and
                   any(c.label == conflict['passage'] for c in claim.citations) for claim in answer.claims):
            answer.claims.append(Claim(text=note, citations=[
                Citation(label=conflict['observation'], quote=conflict['value']),
                Citation(label=conflict['passage'], quote=by_label[conflict['passage']].text.split()[0])]))
        if any(f.source_id == conflict['series'] and f.period == conflict['period'] and
               f.value == Decimal(conflict['planted'].replace(',', '')) for f in figures(answer.summary)):
            answer.summary = ' '.join(c.text for c in answer.claims)
    return answer
