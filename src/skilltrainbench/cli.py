"""stbench CLI for the skill-writing hackathon."""

from __future__ import annotations

import argparse
import asyncio
import json
import os


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="stbench")
    sub = ap.add_subparsers(dest="cmd")
    dp = sub.add_parser("data", help="download the hackathon training tasks")
    dp_sub = dp.add_subparsers(dest="data_cmd")
    pull = dp_sub.add_parser("pull", help="download the training tasks from Hugging Face")
    pull.add_argument("--config", default=None)
    tl = sub.add_parser("tasks", help="list the training task names of a domain")
    tl.add_argument("--domain", required=True)
    tl.add_argument("--config", default=None)
    ev = sub.add_parser("eval", help="evaluate a skill folder with the pinned hackathon learner (local Docker)")
    ev.add_argument("--domain", required=True, help="domain from hackathon.toml (qf, health, tau3, hle)")
    ev.add_argument("--skill", default=None, help="skill folder (contains SKILL.md)")
    ev.add_argument("--arms", default="baseline,skill", help="comma list from baseline,placebo,skill")
    ev.add_argument("--tasks", default="", help="comma-separated task names (default: all training tasks)")
    ev.add_argument("--limit", type=int, default=None, help="evaluate only the first N selected tasks")
    ev.add_argument("--concurrency", type=int, default=None,
                    help="parallel task containers (default: hackathon.toml; lower it on a laptop for qf/tau3)")
    ev.add_argument("--out", required=True)
    ev.add_argument("--config", default=None, help="hackathon config (default: repo-root hackathon.toml)")
    op = sub.add_parser("optimize", help="iteratively generate, score, and promote skill variants")
    op.add_argument("--domain", required=True, help="domain from hackathon.toml")
    op.add_argument("--skill", required=True, help="live skill folder to improve in place")
    op.add_argument("--out", required=True, help="run directory for checkpoints and evaluation artifacts")
    op.add_argument("--iterations", type=int, default=3, help="maximum optimization rounds")
    op.add_argument("--candidates", type=int, default=3, help="variants generated per round")
    op.add_argument("--tasks", default="", help="comma-separated training tasks (default: shuffled selection)")
    op.add_argument("--limit", type=int, default=8, help="total tasks used across tune and validation")
    op.add_argument("--validation-fraction", type=float, default=0.25)
    op.add_argument("--min-improvement", type=float, default=0.0,
                    help="minimum aggregate score gain required for promotion")
    op.add_argument("--seed", type=int, default=0, help="reproducible task split and generation seed")
    op.add_argument("--optimizer-model", default=None,
                    help="review/changer model (default: the pinned learner model)")
    op.add_argument("--optimizer-base-url", default=None,
                    help="OpenAI-compatible review/changer endpoint (default: learner upstream)")
    op.add_argument("--optimizer-key-env", default=None,
                    help="environment variable containing the review/changer API key")
    op.add_argument("--concurrency", type=int, default=None, help="parallel task containers per evaluation")
    op.add_argument("--candidate-parallelism", type=int, default=None,
                    help="candidate evaluations run at once (default: auto within container concurrency)")
    op.add_argument("--keep-candidates", action="store_true", help="retain losing skill folders for debugging")
    op.add_argument("--resume", action="store_true", help="resume a compatible interrupted optimization directory")
    op.add_argument("--config", default=None)
    ck = sub.add_parser("check-skill", help="static submission checks for a skill folder")
    ck.add_argument("skill")
    ck.add_argument("--config", default=None)
    dr = sub.add_parser("doctor", help="check local tools, APIs, and dataset completeness")
    dr.add_argument("--live-api", action="store_true", help="make tiny paid inference calls, not just auth checks")
    dr.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    dr.add_argument("--config", default=None)
    cp = sub.add_parser("compare", help="compare evaluation or optimization result directories")
    cp.add_argument("paths", nargs="+")
    cp.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    cp.add_argument("--config", default=None)
    args = ap.parse_args(argv)
    if args.cmd is None:
        ap.print_help()
        return 1
    return _run(args)


def _run(args) -> int:
    from dotenv import load_dotenv

    from . import config, evaluate

    load_dotenv(config.REPO_ROOT / ".env")
    try:
        hcfg = config.load_config(args.config)
    except (OSError, KeyError, ValueError) as e:
        print(f"cannot load hackathon config: {e}")
        return 2
    try:
        if args.cmd == "check-skill":
            res = config.check_skill(args.skill, hcfg)
            print(json.dumps(res, indent=2))
            return 0 if res["ok"] else 1
        if args.cmd == "tasks":
            print("\n".join(config.task_names(hcfg.domain(args.domain))))
            return 0
        if args.cmd == "data":
            if args.data_cmd != "pull":
                print("usage: stbench data pull")
                return 2
            root = config.pull_data(hcfg, token=os.environ.get("HF_TOKEN"))
            for name, domain in hcfg.domains.items():
                if domain.dataset_dir.is_dir():
                    print(f"{name}: {len(config.task_names(domain))} tasks in {domain.dataset_dir}")
                else:
                    print(f"{name}: no tasks in the download ({domain.dataset_dir} missing)")
            print(f"data in {root}")
            return 0
        if args.cmd == "doctor":
            from .doctor import format_doctor, run_doctor

            result = run_doctor(hcfg, live_api=args.live_api)
            print(json.dumps(result, indent=2) if args.json else format_doctor(result))
            return 0 if all(item["ok"] for item in result["checks"].values()) else 1
        if args.cmd == "compare":
            from .reports import compare_results, format_comparison

            result = compare_results(args.paths)
            print(json.dumps(result, indent=2) if args.json else format_comparison(result))
            return 0
    except ValueError as e:
        print(e)
        return 2

    base = os.environ.get("STBENCH_UPSTREAM_BASE_URL") or hcfg.upstream_base_url
    key = os.environ.get("STBENCH_UPSTREAM_KEY") or os.environ.get(hcfg.upstream_key_env)
    if not key:
        print(f"set {hcfg.upstream_key_env} in .env — this run spends provider credits")
        return 2
    rosetta_warning = _apple_silicon_rosetta_warning()
    if rosetta_warning:
        print(rosetta_warning)
    from . import harbor

    if not harbor.egress_allowlist_supported():
        print("WARNING: this Docker daemon's kernel cannot enforce network allowlists (Docker Desktop lacks "
              "CONFIG_NFT_FIB_INET), so task containers run with public egress here. Scored runs on the "
              "organizers' Linux hosts restrict the learner to the gateway; do not rely on internet access.")
    if args.cmd == "optimize":
        from . import optimize

        task_ids = [t.strip() for t in args.tasks.split(",") if t.strip()] or None
        optimizer_key = key
        if args.optimizer_key_env:
            optimizer_key = os.environ.get(args.optimizer_key_env)
            if not optimizer_key:
                print(f"set {args.optimizer_key_env} for the optimizer model")
                return 2
        try:
            result = asyncio.run(optimize.run_optimization(
                hcfg, args.domain, skill_dir=args.skill, out=args.out,
                iterations=args.iterations, candidates=args.candidates, task_ids=task_ids,
                limit=args.limit, validation_fraction=args.validation_fraction,
                min_improvement=args.min_improvement, seed=args.seed,
                optimizer_model=args.optimizer_model, upstream_base_url=base, upstream_key=key,
                optimizer_base_url=args.optimizer_base_url, optimizer_key=optimizer_key,
                concurrency=args.concurrency, candidate_parallelism=args.candidate_parallelism,
                keep_candidates=args.keep_candidates, resume=args.resume,
            ))
        except (OSError, ValueError, RuntimeError) as e:
            print(e)
            return 2
        print(optimize.format_optimization(result))
        return 0
    if args.skill:
        check = config.check_skill(args.skill, hcfg)
        if not check["ok"]:
            print(json.dumps(check, indent=2))
            return 1
    arms = [a.strip() for a in args.arms.split(",") if a.strip()]
    task_ids = [t.strip() for t in args.tasks.split(",") if t.strip()] or None
    try:
        res = asyncio.run(evaluate.run_eval(
            hcfg, args.domain, skill_dir=args.skill, out=args.out, arms=arms,
            task_ids=task_ids, limit=args.limit, upstream_base_url=base, upstream_key=key,
            concurrency=args.concurrency,
        ))
    except (ValueError, RuntimeError) as e:
        print(e)
        return 2
    print(evaluate.format_result(res))
    print(f"full result: {args.out}/eval_result.json · trajectories: uv run harbor view {args.out}/harbor-jobs")
    return 0


def _apple_silicon_rosetta_warning() -> str | None:
    """Task images are amd64. On Apple Silicon, Docker Desktop's default QEMU
    emulation crashes while the learner agent installs; Rosetta runs them."""
    import platform
    import sys
    from pathlib import Path

    if sys.platform != "darwin" or platform.machine() != "arm64":
        return None
    settings = Path.home() / "Library/Group Containers/group.com.docker/settings-store.json"
    try:
        enabled = json.loads(settings.read_text()).get("UseVirtualizationFrameworkRosetta")
    except (OSError, ValueError):
        return None
    if enabled:
        return None
    return ("WARNING: Docker Desktop's Rosetta emulation is off. Task containers are amd64 and will crash "
            "under the default emulation. Enable Docker Desktop → Settings → General → \"Use Rosetta for "
            "x86_64/amd64 emulation on Apple Silicon\", then Apply & restart.")


if __name__ == "__main__":
    raise SystemExit(main())
