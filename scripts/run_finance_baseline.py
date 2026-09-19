"""Resume the finance baseline, saving each task separately and aggregating scores."""

import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from datetime import datetime, timezone

from skilltrainbench.config import REPO_ROOT, load_config, task_names
from skilltrainbench.tasks import load_task


def write_json(path, value):
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(value, indent=2) + '\n')
    temporary.replace(path)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', default='runs/qf-baseline-all-v1')
    parser.add_argument('--seed', default='runs/qf-baseline-v1/eval_result.json')
    parser.add_argument('--plan', action='store_true')
    args = parser.parse_args()
    os.chdir(REPO_ROOT)
    cfg = load_config()
    domain = cfg.domain('qf')
    names = task_names(domain)
    for name in names:
        load_task(domain.benchmark, domain.dataset_dir, name)
    seed = Path(args.seed).resolve()
    output = Path(args.out).resolve()
    output.mkdir(parents=True, exist_ok=True)
    lock = (output / '.lock').open('w')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    identity = {
        'tasks': names,
        'config_sha256': hashlib.sha256(cfg.path.read_bytes()).hexdigest(),
        'seed': str(seed),
    }
    manifest = output / 'manifest.json'
    if manifest.exists() and json.loads(manifest.read_text()) != identity:
        raise ValueError('Run configuration changed; use a new output directory.')
    seed_status = seed.parent / 'setup_status.json'
    if seed_status.exists():
        assert json.loads(seed_status.read_text())['config_sha256'] == identity['config_sha256']
    write_json(manifest, identity)
    rows = {}
    sources = []

    def include(path):
        result = json.loads(path.read_text())
        assert result['domain'] == 'qf' and result['arms'] == ['baseline']
        assert result['skill_dir'] is None
        assert result['learner']['model'] == cfg.learner_model
        assert result['learner']['agent'] == cfg.harbor_agent
        assert set(result['tasks']) <= set(names)
        assert {row['task_name'] for row in result['per_task']} == set(result['tasks'])
        for row in result['per_task']:
            name = row['task_name']
            assert row['baseline'] in (0, 1) and name not in rows
            rows[name] = {**row, 'source': str(path)}
        sources.append(result)

    include(seed)
    for path in sorted(output.glob('tasks/*/eval_result.json')):
        include(path)

    def report(status, active=None):
        passed = sum(row['baseline'] for row in rows.values())
        costs = [result.get('learner_cost') or {} for result in sources]
        report = {
            'status': status, 'updated_at': datetime.now(timezone.utc).isoformat(),
            'domain': 'qf', 'arms': ['baseline'], 'skill_dir': None,
            'learner': sources[0]['learner'], 'tasks': names,
            'completed_tasks': len(rows), 'total_tasks': len(names),
            'active_task': active, 'passed': passed,
            'baseline_rate': passed / len(rows) if rows else None,
            'learner_tokens': sum(r['learner_usage']['total_tokens'] for r in sources),
            'estimated_usd': sum(c.get('estimated_usd') or 0 for c in costs),
            'cost_incomplete': any(c.get('incomplete', True) for c in costs),
            'per_task': [rows[name] for name in names if name in rows],
            'note': 'Training baseline. Partial rates cover completed tasks only. Costs cover completed evaluations.',
        }
        write_json(output / 'progress.json', report)
        if status == 'complete':
            write_json(output / 'eval_result.json', report)
        print(f'{status}: {len(rows)}/{len(names)} complete; {passed:g} passed; '
              f'active={active}', flush=True)

    remaining = [name for name in names if name not in rows]
    if args.plan:
        print(f'{len(names)} finance tasks; {len(rows)} reused; {len(remaining)} remaining.')
        return
    for name in remaining:
        report('running', name)
        task_output = output / 'tasks' / name
        if task_output.exists():
            suffix = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%f')
            failed = output / 'failed-attempts'
            failed.mkdir(exist_ok=True)
            task_output.rename(failed / f'{name}-{suffix}')
        task_output.mkdir(parents=True)
        command = [sys.executable, '-m', 'skilltrainbench.cli', 'eval',
                   '--domain', 'qf', '--arms', 'baseline', '--tasks', name,
                   '--concurrency', '1', '--out', str(task_output)]
        with (task_output / 'console.log').open('w') as log:
            result = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT)
        if result.returncode:
            report('blocked', name)
            raise RuntimeError(f'Evaluation failed: inspect {task_output / "console.log"}. '
                               'Fix the cause and rerun this command to resume.')
        include(task_output / 'eval_result.json')
    report('complete')


if __name__ == '__main__':
    main()
