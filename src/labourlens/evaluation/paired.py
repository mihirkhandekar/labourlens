"""Paired R3-versus-hybrid comparison with the acceptance rule fixed before the held-out v2 run.

Input is the per-case scored rows written by `labourlens eval` (`experiments/eval/<exp>/<model>.cases.jsonl`).
Nothing here calls a model. Rule (revised before any v2 run after the power simulation in
`experiments/heldout-v2/power.py`; see FREEZE.md and decision D-042):

* the PRIMARY model (`gpt-6-luna`, the model the project ships) decides the headline; every other model is a
  pre-specified replication that is reported and never gates the verdict (so there is no multiplicity to correct);
* both arms must score exactly the same cases for each model (a missing case is an incomplete run, not a pass);
* the paired difference (candidate minus baseline) in behaviour accuracy needs a lower bound above zero at one-sided 95%
  (the lower end of a two-sided 90% interval) under BOTH a case bootstrap and a bootstrap that resamples evidence
  components (cases sharing any acceptable passage or observation id move together; cases without evidence ids are
  their own components);
* at least `min_components` components that carry evidence, so the component interval is not a single draw;
* the candidate may not add false answers for the primary model. Answers contradicting a reference fact are reported,
  not a veto (an AI judge decides them and the simulation did not price that veto).

Source-group clustering is reported as a descriptive, conservative sensitivity only (few groups).
"""

from __future__ import annotations

import hashlib
import json
from collections import defaultdict
from math import comb
from pathlib import Path

import numpy as np

from labourlens import paths

SEED = 20261031
N_BOOT = 20000
LEVEL = 0.90  # two-sided coverage; the lower end is the one-sided 95% bound used by the rule
PRIMARY_MODEL = "gpt-6-luna"
MIN_COMPONENTS = 20
BEHAVIOUR = "behavior_ok"


def load_rows(path: Path) -> dict[str, dict]:
    rows = [json.loads(line) for line in Path(path).read_text().splitlines() if line.strip()]
    return {r["case_id"]: r for r in rows}


def evidence_ids(case: dict) -> set[str]:
    return ({pid for e in case.get("evidence_text", []) for pid in e["passage_ids"]}
            | {oid for e in case.get("evidence_data", []) for oid in e["observation_ids"]})


def components(cases: list[dict]) -> dict[str, str]:
    """Union cases that share an acceptable evidence id. Cases with no evidence ids are singleton components."""
    parent = {c["case_id"]: c["case_id"] for c in cases}

    def find(x: str) -> str:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    owner: dict[str, str] = {}
    for c in cases:
        for ident in evidence_ids(c):
            if ident in owner:
                parent[find(c["case_id"])] = find(owner[ident])
            else:
                owner[ident] = c["case_id"]
    roots = sorted({find(c["case_id"]) for c in cases})
    names = {r: f"component-{i + 1:03d}" for i, r in enumerate(roots)}
    return {c["case_id"]: names[find(c["case_id"])] for c in cases}


def mcnemar_exact(better: int, worse: int) -> float:
    """Two-sided exact binomial (McNemar) p-value on discordant pairs."""
    n = better + worse
    if n == 0:
        return 1.0
    k = min(better, worse)
    tail = sum(comb(n, i) for i in range(k + 1)) / 2**n
    return min(1.0, 2 * tail)


def _interval(diffs: np.ndarray, groups: np.ndarray, n_boot: int, seed: int, level: float) -> list[float]:
    """Resample whole groups; the statistic is the mean difference over the cases in the resampled groups."""
    labels, inverse = np.unique(groups, return_inverse=True)
    sums = np.bincount(inverse, weights=diffs, minlength=len(labels))
    sizes = np.bincount(inverse, minlength=len(labels)).astype(float)
    rng = np.random.default_rng(seed)
    draw = rng.integers(0, len(labels), size=(n_boot, len(labels)))
    stat = sums[draw].sum(axis=1) / sizes[draw].sum(axis=1)
    alpha = 1.0 - level
    lo, hi = np.quantile(stat, [alpha / 2, 1 - alpha / 2])
    return [round(float(lo), 4), round(float(hi), 4)]


def compare(candidate: dict[str, dict], baseline: dict[str, dict], cases: list[dict], source_groups: dict[str, str] | None = None,
            n_boot: int = N_BOOT, seed: int = SEED, level: float = LEVEL, min_components: int = MIN_COMPONENTS,
            exclusions: dict[str, set[str]] | None = None) -> dict:
    expected = sorted(c["case_id"] for c in cases)
    missing = {"candidate": sorted(set(expected) - set(candidate)), "baseline": sorted(set(expected) - set(baseline))}
    extra = {"candidate": sorted(set(candidate) - set(expected)), "baseline": sorted(set(baseline) - set(expected))}
    complete = not any(missing.values()) and not any(extra.values())
    out: dict = {"n_gold_cases": len(expected), "complete": complete, "missing": missing, "unexpected": extra,
                 "seed": seed, "n_boot": n_boot, "level": level}
    if not complete:
        out["conditions"] = {"complete_paired_data": False}
        out["demonstrated_gain"] = False
        return out
    comp = components(cases)
    ids = expected
    diffs = np.array([float(bool(candidate[i][BEHAVIOUR])) - float(bool(baseline[i][BEHAVIOUR])) for i in ids])
    better = int((diffs > 0).sum())
    worse = int((diffs < 0).sum())
    evidence_components = {comp[c["case_id"]] for c in cases if evidence_ids(c)}
    case_groups = np.array(ids)
    comp_groups = np.array([comp[i] for i in ids])
    out.update({
        "behaviour_accuracy": {"candidate": round(float(np.mean([bool(candidate[i][BEHAVIOUR]) for i in ids])), 4),
                               "baseline": round(float(np.mean([bool(baseline[i][BEHAVIOUR]) for i in ids])), 4)},
        "paired_difference": round(float(diffs.mean()), 4), "better": better, "worse": worse,
        "mcnemar_exact_p": round(mcnemar_exact(better, worse), 4),
        "case_bootstrap_interval": _interval(diffs, case_groups, n_boot, seed, level),
        "component_bootstrap_interval": _interval(diffs, comp_groups, n_boot, seed, level),
        "n_components": len(set(comp.values())), "n_evidence_components": len(evidence_components),
    })
    if source_groups:
        groups = np.array([source_groups.get(i, "ungrouped") for i in ids])
        out["source_group_sensitivity_interval"] = _interval(diffs, groups, n_boot, seed, level)
        out["n_source_groups"] = len(set(groups))
    false_c = sum(bool(candidate[i].get("false_answer")) for i in ids)
    false_b = sum(bool(baseline[i].get("false_answer")) for i in ids)
    contra_c = sum(bool(candidate[i].get("facts_contradicted")) for i in ids)
    contra_b = sum(bool(baseline[i].get("facts_contradicted")) for i in ids)
    out["guardrails"] = {"false_answers": {"candidate": false_c, "baseline": false_b},
                         "answers_with_contradicted_fact": {"candidate": contra_c, "baseline": contra_b}}
    by_family: dict[str, dict] = defaultdict(lambda: {"n": 0, "better": 0, "worse": 0})
    family_of = {c["case_id"]: c["family"] for c in cases}
    for i, d in zip(ids, diffs):
        f = by_family[family_of[i]]
        f["n"] += 1
        f["better"] += int(d > 0)
        f["worse"] += int(d < 0)
    out["by_family_descriptive"] = dict(by_family)
    sensitivity = {}
    for name, excluded in (exclusions or {}).items():
        keep = [k for k, i in enumerate(ids) if i not in excluded]
        if len(keep) < 2:
            sensitivity[name] = {"n": len(keep)}
            continue
        sub = diffs[keep]
        sensitivity[name] = {"n": len(keep), "paired_difference": round(float(sub.mean()), 4), "better": int((sub > 0).sum()), "worse": int((sub < 0).sum()),
                             "case_bootstrap_interval": _interval(sub, np.array([ids[k] for k in keep]), n_boot, seed, level)}
    out["sensitivity_descriptive"] = sensitivity
    out["conditions"] = {
        "complete_paired_data": True,
        "case_bootstrap_lower_above_zero": out["case_bootstrap_interval"][0] > 0,
        "component_bootstrap_lower_above_zero": out["component_bootstrap_interval"][0] > 0,
        "enough_evidence_components": len(evidence_components) >= min_components,
        "no_added_false_answers": false_c <= false_b,
    }
    out["demonstrated_gain"] = all(out["conditions"].values())
    return out


def decide(per_model: dict[str, dict], primary: str = PRIMARY_MODEL) -> dict:
    """The primary model decides; other models are reported as replications. Review/reservation gates are checked by a human first."""
    ok = primary in per_model and bool(per_model[primary]["demonstrated_gain"])
    replication = {m: bool(r["demonstrated_gain"]) for m, r in sorted(per_model.items()) if m != primary}
    if primary not in per_model:
        statement = f"Primary model {primary} was not compared; R3 gain NOT demonstrated."
    elif ok:
        statement = f"R3 gain demonstrated for the primary model {primary} under the preregistered rule."
    else:
        statement = f"R3 gain NOT demonstrated for the primary model {primary} under the preregistered rule; report descriptively."
    return {"demonstrated_gain_primary": ok, "primary_model": primary, "replication_models": replication, "models": sorted(per_model),
            "statement": statement}


class GoldMismatch(RuntimeError):
    pass


def check_gold(gold: Path, arms: dict[str, Path], allow_mismatch: bool = False) -> None:
    """Every arm must have been scored (`labourlens eval --gold`) under exactly this gold file."""
    expected = hashlib.sha256(Path(gold).read_bytes()).hexdigest()
    problems = []
    for name, metrics_path in arms.items():
        recorded = json.loads(metrics_path.read_text()).get("provenance", {}).get("gold_sha256") if metrics_path.exists() else None
        if recorded != expected:
            problems.append(f"{name}: scored under {str(recorded)[:12]}, gold file is {expected[:12]}")
    if problems and not allow_mismatch:
        raise GoldMismatch("Paired comparison refused; rescore the arm with `labourlens eval --gold <gold>` or pass --allow-gold-mismatch: " + "; ".join(problems))
    for problem in problems:
        print(f"WARNING (--allow-gold-mismatch): {problem}", flush=True)


def run(gold: Path, candidate_exp: str, baseline_exp: str, models: list[str], out: Path | None = None,
        n_boot: int = N_BOOT, seed: int = SEED, allow_gold_mismatch: bool = False) -> dict:
    eval_dir = paths.EXPERIMENTS / "eval"
    check_gold(gold, {f"{exp}/{m}": eval_dir / exp / f"{m}.metrics.json" for exp in (candidate_exp, baseline_exp) for m in models}, allow_gold_mismatch)
    cases = [json.loads(line) for line in Path(gold).read_text().splitlines() if line.strip()]
    groups = {c["case_id"]: c.get("source_group", "ungrouped") for c in cases}
    exclusions = {"without_mti_ai_feature_group": {c["case_id"] for c in cases if c.get("source_group") == "mti_ai_feature"},
                  "report_text_evidence_cases_only": {c["case_id"] for c in cases if not c.get("evidence_text")}}
    per_model = {}
    for model in models:
        rows = {}
        for role, exp in (("candidate", candidate_exp), ("baseline", baseline_exp)):
            rows[role] = load_rows(paths.EXPERIMENTS / "eval" / exp / f"{model}.cases.jsonl")
        per_model[model] = compare(rows["candidate"], rows["baseline"], cases, groups, n_boot, seed, exclusions=exclusions)
    result = {"gold": str(gold), "candidate": candidate_exp, "baseline": baseline_exp, "per_model": per_model, "decision": decide(per_model)}
    if out is not None:
        Path(out).write_text(json.dumps(result, indent=1) + "\n")
    return result
