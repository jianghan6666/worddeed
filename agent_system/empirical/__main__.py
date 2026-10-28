"""python -m agent_system.empirical --config CONFIG --out RUN [--through step4_prepare]."""

import argparse
import json

from .config import load
from .workflow import STAGES, Workflow


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--through", choices=STAGES, default="step4")
    parser.add_argument("--status", action="store_true")
    parser.add_argument("--agent", action="store_true", help="Let the coordinator call the same stage tools")
    args = parser.parse_args()
    workflow = Workflow(load(args.config), args.out)
    if args.status:
        summary = workflow.status()
    elif args.agent:
        from .coordinator import run
        summary = run(workflow, through=args.through)
    else:
        summary = workflow.execute(args.through)
    print(json.dumps(summary, indent=2))
    return 0 if args.status or summary["status"] in {"ready", "complete", "completed"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
