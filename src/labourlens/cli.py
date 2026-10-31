"""labourlens command line. Milestone 1 commands only: fetch, build, validate, trace, report."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="labourlens")
    sub = p.add_subparsers(dest="cmd", required=True)

    f = sub.add_parser("fetch", help="download official sources into immutable snapshots")
    f.add_argument("--kind", choices=["all", "datasets", "documents"], default="all")
    f.add_argument("--only", nargs="*", help="restrict to these source_ids")

    sub.add_parser("build", help="normalize datasets, extract passages, validate, write reports")

    sub.add_parser("eda", help="generate EDA figures and findings from the validated store")
    sub.add_parser("review-sheets", help="generate unreviewed human spot-check sheets")
    rp = sub.add_parser("review-pack", help="build the private offline owner review pack (no network)")
    rp.add_argument("--tiebreak-dir", help="directory with cards.jsonl and verdicts-*.jsonl (default: private/human-review/tiebreak when present)")
    rp.add_argument("--no-tiebreak", action="store_true", help="ignore any tie-break verdicts")
    ri = sub.add_parser("review-ingest", help="validate owner export; write summary and proposed gold changes only")
    ri.add_argument("results")
    rx = sub.add_parser("retrieval-exp", help="run BM25 experiments on a gold split")
    rx.add_argument("--split", default="dev", choices=["dev", "heldout"])
    dx = sub.add_parser("dense-exp", help="run dense/hybrid embedding experiments (calls the OpenAI embeddings API; needs OPENAI_API_KEY)")
    dx.add_argument("--split", default="dev", choices=["dev", "heldout"])
    r2x = sub.add_parser("retrieval-exp2", help="retrieval improvements R0-R3 (query metadata, LLM rerank); dev only; calls the OpenAI API for rerank")
    r2x.add_argument("--split", default="dev", choices=["dev"])
    r2x.add_argument("--no-rerank", action="store_true", help="run only the API-free configurations")
    ax = sub.add_parser("answer-exp", help="run answer-generation model comparison (calls the OpenAI API)")
    ax.add_argument("--split", default="dev", choices=["dev", "heldout"])
    ax.add_argument("--exp", default="G1", choices=["G1", "G0", "G3", "G4"])
    ax.add_argument("--models", nargs="*", help="restrict to these models")
    ag = sub.add_parser("agent-exp", help="run the end-to-end agent experiment (calls the OpenAI API)")
    ag.add_argument("--split", default="dev", choices=["dev", "heldout"])
    ag.add_argument("--gold", type=Path, help="separate gold JSONL; recorded in generation provenance")
    ag.add_argument("--pairs", nargs="*")
    ag.add_argument("--answer-prompt", default="answer_v3")
    ag.add_argument("--tag", default="A1")
    ag.add_argument("--force", action="store_true", help="overwrite existing raw runs and scores for this experiment id (destroys frozen evidence)")
    ag.add_argument("--planner-prompt", default="planner_v1")
    ag.add_argument("--retrieval", choices=["hybrid", "r3", "r3w"], default="hybrid")
    th = sub.add_parser("threat-test", help="run the adversarial threat suite through the agent (calls the OpenAI API)")
    th.add_argument("--models", nargs="*")
    th.add_argument("--ablation", choices=["naive"], help="run with every defence off, as a baseline")
    th.add_argument("--rescore", action="store_true", help="recompute verdicts from saved raw runs, no API calls")
    th.add_argument("--only", help="a category or case id")
    th.add_argument("--experiment", help="new post-fix experiment id; required for generation (frozen results cannot be overwritten)")
    sub.add_parser("mcp-demo", help="run the scripted MCP client demo and write docs/mcp-demo-transcript.md")
    ev_ = sub.add_parser("eval", help="metrics from saved raw agent runs; judged measures call the OpenAI API")
    ev_.add_argument("--exp", default="agent-dev-A1")
    ev_.add_argument("--split", default="dev")
    ev_.add_argument("--gold", type=Path, help="same gold JSONL used for generation")
    ev_.add_argument("--labels", nargs="*")
    ev_.add_argument("--allow-gold-mismatch", action="store_true", help="rescore a run under a gold file different from the one recorded for it (loud warning)")
    ev_.add_argument("--no-judge", action="store_true")
    ev_.add_argument("--rejudge-stale", action=argparse.BooleanOptionalAction, default=True,
                     help="re-judge cached judgments whose input fingerprint changed (default); --no-rejudge-stale raises instead")
    pr = sub.add_parser("paired", help="preregistered paired comparison of two scored experiments (no model calls)")
    pr.add_argument("--gold", type=Path, required=True)
    pr.add_argument("--candidate", required=True, help="scored experiment id, e.g. agent-heldout-V2-r3")
    pr.add_argument("--baseline", required=True, help="scored experiment id, e.g. agent-heldout-V2-hybrid")
    pr.add_argument("--models", nargs="+", required=True)
    pr.add_argument("--allow-gold-mismatch", action="store_true", help="accept arms scored under a different gold file (loud warning)")
    pr.add_argument("--out", type=Path)
    pr.add_argument("--n-boot", type=int, default=20000)
    pr.add_argument("--seed", type=int, default=20261031)
    sub.add_parser("audit-report", help="summarise the audit and feedback logs (data/audit)")
    asw = sub.add_parser("audit-show", help="print the timeline of one run")
    asw.add_argument("run_id")
    ap = sub.add_parser("audit-prune", help="delete audit run logs older than N days")
    ap.add_argument("--days", type=int, required=True)
    sub.add_parser("scan-sources", help="scan stored passages and statistics text fields for instruction-like content (no build, no network)")
    sub.add_parser("gold-check", help="validate the gold set and regenerate the owner review sheet")
    sub.add_parser("export", help="export presentation-ready JSON for the interactive report page")
    sub.add_parser("build-report", help="assemble the rights-safe interactive presentation")
    serve = sub.add_parser("serve", help="serve the presentation and authenticated live demo")
    serve.add_argument("--host", default="127.0.0.1")
    serve.add_argument("--port", type=int, default=8000)
    sub.add_parser("rights-scan", help="fail if tracked files quote more than six consecutive words of any local MOM/MTI passage")
    sub.add_parser("revisions", help="report historical-value changes between dataset snapshots")

    t = sub.add_parser("trace", help="print provenance for an observation_id or passage_id")
    t.add_argument("id")

    args = p.parse_args(argv)
    if args.cmd in ("review-pack", "review-ingest"):
        from labourlens.review.pack import build_pack, ingest_review

        try:
            if args.cmd == "review-pack":
                print(build_pack(tiebreak_dir=Path(args.tiebreak_dir) if args.tiebreak_dir else None, use_tiebreak=not args.no_tiebreak))
            else:
                for output in ingest_review(Path(args.results)):
                    print(output)
        except ValueError as exc:
            print(f"Review error: {exc}", file=sys.stderr)
            return 2
        return 0
    if args.cmd == "fetch":
        from labourlens.data import fetch

        fetch.run(args.kind, args.only)
        return 0
    if args.cmd == "build":
        from labourlens.data import build

        return build.run()
    if args.cmd == "eda":
        from labourlens.data import eda

        eda.run()
        return 0
    if args.cmd == "review-sheets":
        from labourlens.data import review

        review.run()
        return 0
    if args.cmd == "retrieval-exp":
        from labourlens.retrieval import experiments

        experiments.run(args.split)
        return 0
    if args.cmd == "dense-exp":
        from labourlens.retrieval import experiments_dense

        experiments_dense.run(args.split)
        return 0
    if args.cmd == "retrieval-exp2":
        from labourlens.retrieval import experiments_rerank

        experiments_rerank.run(args.split, not args.no_rerank)
        return 0
    if args.cmd == "answer-exp":
        from labourlens.answer import experiments as ae

        ae.run(args.split, args.models, args.exp)
        return 0
    if args.cmd == "agent-exp":
        from labourlens.agent import experiments as agx

        agx.run(args.split, args.pairs, args.answer_prompt, args.tag, args.retrieval, args.planner_prompt, gold_path=args.gold, force=args.force)
        return 0
    if args.cmd == "threat-test":
        from labourlens.security import threat_suite

        threat_suite.rescore(args.experiment) if args.rescore else threat_suite.run(args.models, args.only, args.ablation, args.experiment)
        return 0
    if args.cmd == "mcp-demo":
        from labourlens.mcp import demo

        demo.run()
        return 0
    if args.cmd == "eval":
        from labourlens.evaluation import harness

        harness.run(args.exp, args.split, args.labels, not args.no_judge, rejudge_stale=args.rejudge_stale, gold_path=args.gold,
                    allow_gold_mismatch=args.allow_gold_mismatch)
        return 0
    if args.cmd == "paired":
        import json as _json

        from labourlens.evaluation import paired

        result = paired.run(args.gold, args.candidate, args.baseline, args.models, args.out, args.n_boot, args.seed, args.allow_gold_mismatch)
        print(_json.dumps(result, indent=1))
        return 0
    if args.cmd in ("audit-report", "audit-show", "audit-prune"):
        from labourlens.audit import log as al

        print(al.report() if args.cmd == "audit-report" else al.show(args.run_id) if args.cmd == "audit-show" else al.prune(args.days))
        return 0
    if args.cmd == "scan-sources":
        import json as _j
        from types import SimpleNamespace

        import pandas as _pd

        from labourlens import paths as _p
        from labourlens.data import validate as _v

        ps = [SimpleNamespace(**{"passage_id": d["passage_id"], "text": d["text"]}) for f in sorted(_p.PASSAGES.glob("*.jsonl")) for d in map(_j.loads, f.read_text().splitlines()) ]
        r = _v.scan_injection(ps, _pd.read_parquet(_p.PROCESSED / "observations.parquet"))
        print(_j.dumps({k: (v if k != "hits" else v[:20]) for k, v in r.items()}, indent=1), f"\nhits: {len(r['hits'])}")
        return 1 if r["hits"] else 0
    if args.cmd == "gold-check":
        from labourlens import paths as _p
        from labourlens.retrieval import gold

        errs = gold.validate()
        for e in errs:
            print("ERROR", e)
        if not errs:
            (_p.ROOT / "docs" / "human-review" / "gold-review.md").write_text(gold.review_sheet())
            print("gold set valid; wrote docs/human-review/gold-review.md")
        return 1 if errs else 0
    if args.cmd == "export":
        from labourlens.data import export

        export.run()
        return 0
    if args.cmd == "build-report":
        from labourlens.report import build as report_build

        report_build.run()
        return 0
    if args.cmd == "serve":
        from labourlens.report.serve import run

        run(args.host, args.port)
        return 0
    if args.cmd == "rights-scan":
        from labourlens.data import rights_scan

        return rights_scan.run()
    if args.cmd == "revisions":
        from labourlens.data import revisions

        return revisions.run()
    if args.cmd == "trace":
        from labourlens.data import trace

        return trace.run(args.id)
    return 2


if __name__ == "__main__":
    sys.exit(main())
