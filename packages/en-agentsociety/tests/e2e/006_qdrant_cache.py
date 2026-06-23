import argparse
import logging
from pathlib import Path

from utils import build_clickhouse_config, ensure_config_exists, run_society, run_with_ray, start_clickhouse_container
from en_agentsociety.llm.cache.ray_actor import _sanitize_collection_name

DEFAULT_CONFIG = Path(__file__).parent / "configs/006_qdrant_cache.yaml"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="AgentSociety Qdrant cache shadow-mode end-to-end test"
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=DEFAULT_CONFIG,
        help=f"Path to YAML config file (default: {DEFAULT_CONFIG})",
    )
    return parser.parse_args()

def main() -> None:
    args = parse_args()

    ensure_config_exists(args.config)

    logging.basicConfig(level=logging.INFO)

    with start_clickhouse_container() as (host, port):
        config = build_clickhouse_config(args.config, host, port)
        config.env.qdrant_cache.enabled = True
        # Shadow mode: always run live LLM and only probe/learn from cache.
        config.env.qdrant_cache.skip_mode = False

        qdrant_path = Path(
            config.env.qdrant_cache.path or Path(config.env.data_dir) / "qdrant"
        )
        if not qdrant_path.is_absolute():
            # Ray workers run from repo root runtime_env; anchor cache path explicitly.
            qdrant_path = (Path(__file__).parent / qdrant_path).resolve()
        config.env.qdrant_cache.path = str(qdrant_path)
        stats_path = qdrant_path / f"stats_{_sanitize_collection_name(str(config.exp.id))}.json"

        try:
            run_with_ray(run_society(config))
            if not stats_path.exists():
                raise RuntimeError(
                    f"Qdrant cache stats file was not created at {stats_path}."
                )
            logging.info(
                "E2E Qdrant shadow-mode cache test PASSED — simulation completed and cache stats were persisted."
            )
        except Exception as e:
            logging.exception(f"E2E Qdrant shadow-mode cache test FAILED: {e}")
            raise SystemExit(1) from e


if __name__ == "__main__":
    main()