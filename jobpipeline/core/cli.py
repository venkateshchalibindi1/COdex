from __future__ import annotations

import argparse

from jobpipeline.core.orchestrator import PipelineOrchestrator
from jobpipeline.utils.config import load_config
from jobpipeline.utils.logging_utils import setup_logging


def main() -> None:
    parser = argparse.ArgumentParser(description="Run JobPipeline pipeline")
    parser.add_argument("--config", default="config.yaml")
    args = parser.parse_args()
    setup_logging()
    config = load_config(args.config)
    counts = PipelineOrchestrator(config).run()
    print("Run complete:", counts)


if __name__ == "__main__":
    main()
