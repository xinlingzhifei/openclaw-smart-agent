import argparse
from pathlib import Path

import uvicorn

from openclaw_smart_agent.api import create_app
from openclaw_smart_agent.config import dump_runtime_config, load_runtime_config
from openclaw_smart_agent.runtime import SmartAgentRuntime


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="openclaw-smart-agent")
    subparsers = parser.add_subparsers(dest="command", required=True)

    serve = subparsers.add_parser("serve", help="Run the Smart Agent API server")
    serve.add_argument("--host", default="127.0.0.1")
    serve.add_argument("--port", type=int, default=8787)
    serve.add_argument("--db-path", default="data/smart-agent.db")
    serve.add_argument("--template-dir", default=None)
    serve.add_argument("--config", default="config/config.yaml")

    init_config = subparsers.add_parser("init-config", help="Copy the example config to a writable location")
    init_config.add_argument("--output", default="config/config.yaml")

    return parser


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "init-config":
        destination = Path(args.output)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(dump_runtime_config(), encoding="utf-8")
        print(f"Config written to {destination}")
        return

    runtime = SmartAgentRuntime(
        db_path=args.db_path,
        template_dir=args.template_dir,
        config=load_runtime_config(args.config) if Path(args.config).exists() else None,
    )
    uvicorn.run(create_app(runtime), host=args.host, port=args.port)
