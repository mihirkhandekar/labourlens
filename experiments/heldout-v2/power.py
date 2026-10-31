"""Monte Carlo power and false-positive rate of candidate acceptance rules for held-out v2.

No model output is used: paired per-case outcomes are simulated on the real 65-case gold structure (39 evidence
components from `labourlens.evaluation.paired.components`). Deterministic: every simulation uses a generator seeded from
SEED and its index. Run: `uv run python experiments/heldout-v2/power.py > experiments/heldout-v2/power.txt`.

Simulation model (ASSUMPTIONS, stated in docs/experiments/m7-heldout-v2-design.md):
* per case, R3 is better than hybrid with probability pb, worse with probability pw, otherwise the arms agree;
  pw is fixed at 0.04 and pb = effect + pw, so the true paired effect is `effect`; "null-busy" uses pb = pw = 0.10;
* scenario "uniform": every one of the 65 cases can flip; "report-text": only the 34 answerable cases whose gold evidence
  is report text can flip (the other 31 are insensitive to retrieval), with pb/pw scaled so the expected paired effect
  over all 65 cases is still `effect`;
* clustering: each evidence component is, with probability RHO, "coupled" (all its cases draw one shared outcome), else
  its cases draw independently; RHO=0 is no clustering, RHO=0.5 is substantial;
* the false-answer guard counts non-answer cases (21) where R3 flips: a worse flip adds one false answer, a better flip
  removes one; the guard fails when added exceeds removed. The reference-contradiction guard is not simulated;
* the two models are independent replicates (real models share cases and retrieval, so they are positively correlated).
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from labourlens.evaluation.paired import components

ROOT = Path(__file__).resolve().parents[2]
GOLD = ROOT / "experiments" / "gold" / "heldout_v2_draft.jsonl"
SEED = 20261101
N_SIM = 2000
N_BOOT = 1000
PW = 0.04
EFFECTS = [0.0, 0.05, 0.10, 0.16]
RHOS = [0.0, 0.5]

cases = [json.loads(line) for line in GOLD.read_text().splitlines() if line.strip()]
ids = [c["case_id"] for c in cases]
comp = components(cases)
comp_idx = np.unique([comp[i] for i in ids], return_inverse=True)[1]
n, n_comp = len(ids), int(comp_idx.max()) + 1
answerable = np.array([c["expected_behavior"] in ("answer", "ignore_injection_and_answer") for c in cases])
sensitive = np.array([bool(c.get("evidence_text")) and a for c, a in zip(cases, answerable)])
non_answer = ~answerable
n_evidence_components = len({comp[c["case_id"]] for c in cases if c.get("evidence_text") or c.get("evidence_data")})
sizes = np.bincount(comp_idx).astype(float)


def draw_outcomes(rng, pb, pw, rho, can_flip):
    """+1 better, -1 worse, 0 same per case."""
    u_case = rng.random(n)
    u_comp = rng.random(n_comp)[comp_idx]
    coupled = (rng.random(n_comp) < rho)[comp_idx]
    u = np.where(coupled, u_comp, u_case)
    out = np.where(u < pb, 1, np.where(u < pb + pw, -1, 0))
    return np.where(can_flip, out, 0)


def lower_bounds(diffs, rng, q):
    """Lower percentile-bootstrap bound of the mean difference for case and component resampling."""
    res = []
    draw = rng.integers(0, n, size=(N_BOOT, n))
    res.append(np.quantile(diffs[draw].mean(axis=1), q))
    sums = np.bincount(comp_idx, weights=diffs, minlength=n_comp)
    d = rng.integers(0, n_comp, size=(N_BOOT, n_comp))
    res.append(np.quantile(sums[d].sum(axis=1) / sizes[d].sum(axis=1), q))
    return res


def one_model(rng, effect, scenario, rho, busy=False):
    can = np.ones(n, bool) if scenario == "uniform" else sensitive
    scale = n / can.sum()  # concentrate the same expected effect on the cases that can move
    pw0 = 0.10 if busy else PW
    pb0 = 0.10 if busy else effect + PW
    pb, pw = pb0 * scale, pw0 * scale
    diffs = draw_outcomes(rng, pb, pw, rho, can)
    lo975 = lower_bounds(diffs.astype(float), rng, 0.025)   # two-sided 97.5%
    lo95 = lower_bounds(diffs.astype(float), rng, 0.05)     # one-sided 95%
    guard_ok = (diffs[non_answer] < 0).sum() <= (diffs[non_answer] > 0).sum()
    return {"old": lo975[0] > 0 and lo975[1] > 0, "one": lo95[0] > 0 and lo95[1] > 0, "guard": bool(guard_ok)}


def cell(effect, scenario, rho, busy=False):
    rng_base = np.random.SeedSequence([SEED, int(effect * 1000), 1 if scenario == "uniform" else 2, int(rho * 10), int(busy)])
    seeds = rng_base.spawn(N_SIM)
    tot = dict.fromkeys(["R0_both_975_guard", "R1_both_95_guard", "R2_primary_95", "R2_primary_95_guard_reported_pass", "R3_either_95", "R4_both_95_noveto", "single_model_975_noguard"], 0)
    for s in seeds:
        rng = np.random.default_rng(s)
        m = [one_model(rng, effect, scenario, rho, busy) for _ in range(2)]
        tot["R0_both_975_guard"] += all(x["old"] and x["guard"] for x in m)
        tot["R1_both_95_guard"] += all(x["one"] and x["guard"] for x in m)
        tot["R2_primary_95"] += m[0]["one"]
        tot["R2_primary_95_guard_reported_pass"] += m[0]["one"] and m[0]["guard"]
        tot["R3_either_95"] += any(x["one"] for x in m)
        tot["R4_both_95_noveto"] += all(x["one"] for x in m)
        tot["single_model_975_noguard"] += m[0]["old"]
    return {k: v / N_SIM for k, v in tot.items()}


def main():
    print(f"gold {GOLD.name}: {n} cases, {n_comp} components ({n_evidence_components} carry evidence), {int(sensitive.sum())} report-text answerable, {int(non_answer.sum())} non-answer")
    print(f"seed {SEED}, {N_SIM} simulations per cell, {N_BOOT} bootstrap resamples, pw={PW} (null-busy: pb=pw=0.10); Monte Carlo SE about 0.01 (0.005 near 0 or 1)\n")
    cols = ["R0_both_975_guard", "R1_both_95_guard", "R4_both_95_noveto", "R3_either_95", "R2_primary_95", "R2_primary_95_guard_reported_pass", "single_model_975_noguard"]
    print("rule columns: R0 current (both models, 97.5% two-sided, guard veto); R1 both models 95% one-sided + guard veto; R4 both 95% one-sided no veto;")
    print("R3 either model 95% one-sided; R2 primary model only 95% one-sided (guard reported); same with guard passing; single_model_975 current interval, one model.\n")
    print("| scenario | rho | true effect | " + " | ".join(cols) + " |")
    print("|---|---|---|" + "---|" * len(cols))
    for scenario in ("uniform", "report-text"):
        for rho in RHOS:
            for effect in EFFECTS:
                r = cell(effect, scenario, rho)
                label = f"{effect:+.2f}" + (" (null)" if effect == 0 else "")
                print(f"| {scenario} | {rho} | {label} | " + " | ".join(f"{r[c]:.3f}" for c in cols) + " |")
            r = cell(0.0, scenario, rho, busy=True)
            print(f"| {scenario} | {rho} | 0 (null, busy: pb=pw=0.10) | " + " | ".join(f"{r[c]:.3f}" for c in cols) + " |")


if __name__ == "__main__":
    main()
