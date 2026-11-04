"""Deterministic answer checks (D-024). Hard errors make an answer invalid; soft findings are reported."""

from __future__ import annotations

import html
import re
import unicodedata
from dataclasses import dataclass, field

from labourlens.answer.context import ContextPassage
from labourlens.answer.schema import Answer

MAX_QUOTE_WORDS = 40
_NUM = re.compile(r"\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+\.\d+|\d+")
_YEAR = re.compile(r"^(?:19|20)\d\d$")


def annual_missing_quarter_abstention(answer: Answer, trace: list[dict]) -> Answer:
    """Make a served annual abstention explain a tool's specific incomplete-year refusal.

    Only typed not_found annual_average errors with the missing-quarters marker
    qualify. Ignore a failure superseded by a successful call with the same filters.
    Never rewrite an answered/refused/clarify reply or infer unpublished quarters.
    """
    if answer.status != "abstained":
        return answer
    failures: dict[str, set[str]] = {}
    for event in trace:
        detail = event.get("detail") or {}
        if event.get("node") != "execute_tool" or detail.get("tool") != "annual_average":
            continue
        key = repr(sorted((detail.get("args") or {}).items()))
        if event.get("event") == "ok":
            failures.pop(key, None)
        elif event.get("event") == "error" and detail.get("error_kind") == "not_found":
            message = str(detail.get("message") or "")
            if "missing quarters:" in message:
                missing = re.findall(r"\b20\d\d-Q[1-4]\b", message.split("missing quarters:", 1)[1])
                if missing:
                    failures[key] = set(missing)
    quarters = sorted(set().union(*failures.values())) if failures else []
    if not quarters:
        return answer
    reason = (f"Missing quarterly rates: {', '.join(quarters)}. "
              "No annual-average figure can be computed until those quarterly rates are published; a partial-year average is not used.")
    return answer.model_copy(update={"reason": reason})

# Served annual rights boundary (shared by the validator and the web projection): no RIGHTS_RUN_WORDS consecutive normalised words
# of a report passage may appear in the model's own prose. Tokens are letters and digits only, NFKC case-folded.
RIGHTS_RUN_WORDS = 7
RIGHTS_TOKEN = re.compile(r"[^\W_]+")
_ENTITY = re.compile(r"&(?:#[xX][0-9a-fA-F]+;?|#[0-9]+;?|[A-Za-z][A-Za-z0-9]+;?)")


def rights_tokens(value) -> list[tuple[str, int, int]]:
    """Normalized words with offsets into the original text, for local span removal.

    Ignore formatting-only characters, but retain punctuation as word boundaries.
    Offsets survive NFKC expansions and case folding (including full-width text).
    """
    text = str(value or "")
    normalized, offsets = [], []
    # Decode entities while retaining offsets into the original text for clause
    # removal and six-word public prefixes. Each decoded character maps to its
    # complete source entity, so a prefix never cuts an entity in half.
    units, last = [], 0
    for match in _ENTITY.finditer(text):
        units.extend((char, i, i + 1) for i, char in enumerate(text[last:match.start()], last))
        units.extend((char, match.start(), match.end()) for char in html.unescape(match.group()))
        last = match.end()
    units.extend((char, i, i + 1) for i, char in enumerate(text[last:], last))
    for char, start, end in units:
        if unicodedata.category(char) == "Cf":
            continue
        for folded in unicodedata.normalize("NFKC", char).casefold():
            normalized.append(folded)
            offsets.append((start, end))
    return [(m.group(), offsets[m.start()][0], offsets[m.end() - 1][1]) for m in RIGHTS_TOKEN.finditer("".join(normalized))]


def report_windows(texts) -> set[tuple[str, ...]]:
    n = RIGHTS_RUN_WORDS
    windows: set[tuple[str, ...]] = set()
    for text in texts:
        words = [word for word, _, _ in rights_tokens(text)]
        windows.update(tuple(words[i:i + n]) for i in range(len(words) - n + 1))
    return windows


def copied_spans(value, windows) -> list[tuple[int, int]]:
    """Merged (start, end) character spans of ``value`` that reproduce RIGHTS_RUN_WORDS or more consecutive report words."""
    n = RIGHTS_RUN_WORDS
    tokens = rights_tokens(value)
    spans: list[tuple[int, int]] = []
    for i in range(len(tokens) - n + 1):
        if tuple(t[0] for t in tokens[i:i + n]) not in windows:
            continue
        start, end = tokens[i][1], tokens[i + n - 1][2]
        if spans and start <= spans[-1][1]:
            spans[-1] = (spans[-1][0], max(spans[-1][1], end))
        else:
            spans.append((start, end))
    return spans


def report_copy_errors(answer: Answer, ctx: list[ContextPassage]) -> list[str]:
    """Served annual mode: free-text fields must paraphrase report passages. Each error lists only the offending run, which is the
    model's own wording; no source text beyond it. Citation quotes are exempt (the projection cuts them to six words)."""
    windows = report_windows(p.text for p in ctx if p.label.startswith("P"))
    if not windows:
        return []
    fields = [("summary", answer.summary), ("reason", answer.reason), ("clarification_question", answer.clarification_question),
              *((f"caveats[{i}]", c) for i, c in enumerate(answer.caveats)), *((f"claims[{i}].text", c.text) for i, c in enumerate(answer.claims))]
    errors = []
    for name, value in fields:
        for start, end in copied_spans(value, windows):
            errors.append(f'{name} copies a run of report wording: "{value[start:end][:300]}"; paraphrase it in your own words '
                          f"(never copy {RIGHTS_RUN_WORDS} or more consecutive words from a report passage; short exact quotes belong only in a citation quote)")
    return errors


def norm(t: str) -> str:
    t = unicodedata.normalize("NFKC", html.unescape(t))
    t = t.translate({0x2018: "'", 0x2019: "'", 0x201C: '"', 0x201D: '"', 0x2013: "-", 0x2014: "-", 0x00A0: " "})
    return re.sub(r"\s+", " ", t).strip().casefold()


def quote_in(quote: str, text: str) -> bool:
    """The single definition of 'quote is verbatim in text', shared by the validator and the web projection.

    HTML entities, case, NFKC, curly quotes, dashes and whitespace (including PDF hard line breaks) are ignored on both sides."""
    q = norm(quote)
    return bool(q) and q in norm(text)


def numbers(text: str) -> set[str]:
    """Numeric tokens with thousands separators removed. Years are dropped; they are not figures."""
    out = set()
    for m in _NUM.findall(text):
        v = m.replace(",", "")
        if not _YEAR.match(v):
            out.add(v)
    return out


def key_numbers(text: str) -> set[str]:
    """Figures worth requiring in an answer: decimals, comma-grouped numbers, or integers of 100 or more (not years)."""
    return {n for n in numbers(text) if "." in n or (n.isdigit() and int(n) >= 100)}


@dataclass
class Report:
    errors: list[str] = field(default_factory=list)
    ungrounded_numbers: list[str] = field(default_factory=list)
    cited_passage_ids: list[str] = field(default_factory=list)

    @property
    def valid(self) -> bool:
        return not self.errors


_WHY = re.compile(r"\b(?:why|reasons?|drivers?|caused?|causes?|explain|explanation|because|attribut\w+)\b", re.I)
_SEARCH_FAILURE_SAID = re.compile(r"\b(?:report|reports|commentary|explanation|explanations)\b.*\b(?:search|searches|unavailable|could not|timed out|failed|not covered|not retrieved)\b"
                                  r"|\b(?:search|timed out|failed)\b.*\b(?:report|reports|commentary)\b", re.I | re.S)


def report_search_failure_errors(answer: Answer, question: str, reason: str) -> list[str]:
    """Served mode: when report search timed out or failed, no report passage came back and the question asks for reasons, an answered
    reply must say so in its summary or caveats; a statistics-only answer must not read as complete."""
    if answer.status != "answered" or not _WHY.search(question or ""):
        return []
    said = " ".join([answer.summary, *answer.caveats])
    return [] if _SEARCH_FAILURE_SAID.search(said) else [
        f"report search {reason} and the question asks for reasons, but the answer does not say that report evidence could not be collected; "
        "state this in the caveats and answer only what the statistics show"]


def missing_period_errors(answer: Answer, ctx: list[ContextPassage]) -> list[str]:
    """Narrow contradiction check for served abstentions, not a semantic judge.

    Only explicit 'no data for YYYY-Qn' assertions about quarterly statistics are
    checked. Report commentary may genuinely be absent despite an O item.
    Missing-value observations never prove that a published value exists.
    """
    if answer.status != "abstained":
        return []
    present = {p for item in ctx if item.label.startswith("O") and not item.flags and "no published number" not in item.text.casefold()
               for p in re.findall(r"\b20\d\d-Q[1-4]\b", item.text)}
    pattern = r"\bno (?:quarterly )?(?:data|observations|statistics|figures|values)(?: (?:is|are) available)? (?:for|in) (20\d\d-Q[1-4])\b"
    denied = {p.upper() for p in re.findall(pattern, answer.reason, re.I)}
    return [f"abstention says no data for {p}, but a published observation for that quarter is supplied; identify the missing method, series or commentary instead"
            for p in sorted(denied & present)]


def check(answer: Answer, ctx: list[ContextPassage]) -> Report:
    by_label = {p.label: p for p in ctx}
    rep = Report()
    cited: list[str] = []
    if answer.status == "answered":
        if not answer.claims:
            rep.errors.append("status is answered but there are no claims")
        if not answer.summary.strip():
            rep.errors.append("status is answered but the summary is empty")
    else:
        if answer.claims:
            rep.errors.append(f"status is {answer.status} but claims were given")
        if not answer.reason.strip():
            rep.errors.append(f"status is {answer.status} but no reason was given")
    if answer.status == "clarify" and not answer.clarification_question.strip():
        rep.errors.append("status is clarify but no clarification question was given")
    for i, c in enumerate(answer.claims):
        if not c.citations:
            rep.errors.append(f"claim {i + 1} has no citation")
        support = []
        for cit in c.citations:
            p = by_label.get(cit.label)
            if p is None:
                rep.errors.append(f"claim {i + 1} cites {cit.label!r}, which was not in the context")
                continue
            if p.flags:
                rep.errors.append(f"claim {i + 1} cites {cit.label}, which is flagged as containing instructions and cannot be used as evidence")
            if len(cit.quote.split()) > MAX_QUOTE_WORDS:
                rep.errors.append(f"claim {i + 1} quote from {cit.label} is longer than {MAX_QUOTE_WORDS} words")
            if not quote_in(cit.quote, p.text):
                rep.errors.append(f"claim {i + 1} quote is not verbatim in {cit.label}")
            else:
                cited.append(p.passage_id)
                support.append(norm(p.text))
        bad = sorted(n for n in numbers(c.text) if not any(n in numbers(s) for s in support))
        rep.ungrounded_numbers += [f"claim {i + 1}: {n}" for n in bad]
    # Summary and caveats are free text too: every key figure (decimals, comma-grouped numbers, integers of 100 or more; not years,
    # quarter numbers or small counts) must appear somewhere in the evidence the model was given.
    context_numbers = set().union(*(numbers(p.text) for p in ctx)) if ctx else set()
    free = [("summary", answer.summary), *[(f"caveat {i + 1}", t) for i, t in enumerate(answer.caveats)]]
    for where, text in free:
        rep.ungrounded_numbers += [f"{where}: {n}" for n in sorted(key_numbers(text) - context_numbers)]
    rep.cited_passage_ids = list(dict.fromkeys(cited))
    return rep


def recover_quote_errors(answer: Answer, ctx: list[ContextPassage], errors: list[str]) -> Answer | None:
    """Served-only, after repair: discard bad quotes/unsupported claims, never bypass other errors.

    This availability tradeoff retains a possibly less-supported summary with a
    visible caveat. It is not semantic verification of the surviving claims.
    """
    allowed = r"claim \d+ quote (?:is not verbatim in \S+|from \S+ is longer than \d+ words)"
    if answer.status != "answered" or not errors or any(not re.fullmatch(allowed, error) for error in errors):
        return None
    by_label = {p.label: p for p in ctx}
    claims = []
    for claim in answer.claims:
        citations = [c for c in claim.citations if c.label in by_label and not by_label[c.label].flags
                     and len(c.quote.split()) <= MAX_QUOTE_WORDS and quote_in(c.quote, by_label[c.label].text)]
        if citations:
            claims.append(claim.model_copy(update={"citations": citations}))
    if not claims:
        return None
    caveat = "Some supporting quotes could not be verified and were removed."
    candidate = answer.model_copy(update={"claims": claims, "caveats": list(dict.fromkeys([*answer.caveats, caveat]))})
    checked = check(candidate, ctx)
    return candidate if not checked.errors and not any(n.startswith("claim ") for n in checked.ungrounded_numbers) else None
