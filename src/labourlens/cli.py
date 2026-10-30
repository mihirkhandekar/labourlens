"""labourlens command line. Milestone 1 commands only: fetch, build, validate, trace, report."""

from __future__ import annotations

import argparse
import sys


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="labourlens")
    sub = p.add_subparsers(dest="cmd", required=True)

    f = sub.add_parser("fetch", help="download official sources into immutable snapshots")
    f.add_argument("--kind", choices=["all", "datasets", "documents"], default="all")
    f.add_argument("--only", nargs="*", help="restrict to these source_ids")

    sub.add_parser("build", help="normalize datasets, extract passages, validate, write reports")

    sub.add_parser("eda", help="generate EDA figures and findings from the validated store")
    sub.add_parser("review-sheets", help="generate unreviewed human spot-check sheets")
    rx = sub.add_parser("retrieval-exp", help="run BM25 experiments on a gold split")
    rx.add_argument("--split", default="dev", choices=["dev", "heldout"])
    dx = sub.add_parser("dense-exp", help="run dense/hybrid embedding experiments (calls the OpenAI embeddings API; needs OPENAI_API_KEY)")
    dx.add_argument("--split", default="dev", choices=["dev", "heldout"])
    ax = sub.add_parser("answer-exp", help="run answer-generation model comparison (calls the OpenAI API)")
    ax.add_argument("--split", default="dev", choices=["dev", "heldout"])
    ax.add_argument("--exp", default="G1", choices=["G1", "G0", "G3", "G4"])
    ax.add_argument("--models", nargs="*", help="restrict to these models")
    sub.add_parser("gold-check", help="validate the gold set and regenerate the owner review sheet")
    sub.add_parser("export", help="export presentation-ready JSON for the interactive report page")
    sub.add_parser("revisions", help="report historical-value changes between dataset snapshots")

    t = sub.add_parser("trace", help="print provenance for an observation_id or passage_id")
    t.add_argument("id")

    args = p.parse_args(argv)
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
    if args.cmd == "answer-exp":
        from labourlens.answer import experiments as ae

        ae.run(args.split, args.models, args.exp)
        return 0
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
    if args.cmd == "revisions":
        from labourlens.data import revisions

        return revisions.run()
    if args.cmd == "trace":
        from labourlens.data import trace

        return trace.run(args.id)
    return 2


if __name__ == "__main__":
    sys.exit(main())
