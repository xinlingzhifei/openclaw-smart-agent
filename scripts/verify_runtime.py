#!/usr/bin/env python3
import argparse
import json
import sys
import urllib.error
import urllib.request


def request_json(base_url: str, path: str, payload: dict | None = None) -> dict:
    data = None
    headers = {}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["content-type"] = "application/json"

    request = urllib.request.Request(f"{base_url}{path}", data=data, headers=headers)
    with urllib.request.urlopen(request) as response:
        return json.loads(response.read().decode("utf-8"))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Verify the OpenClaw Smart Agent runtime API flow.")
    parser.add_argument("--base-url", default="http://127.0.0.1:8787")
    parser.add_argument("--identity", default="Python开发")
    args = parser.parse_args(argv)

    try:
        created = request_json(
            args.base_url,
            "/api/v1/agents/create",
            {"identity": args.identity},
        )
        agent_id = created["agent"]["agent_id"]

        heartbeat = request_json(
            args.base_url,
            "/api/v1/agents/heartbeat",
            {
                "agent_id": agent_id,
                "cpu_percent": 18.0,
                "memory_percent": 27.0,
                "consecutive_errors": 0,
                "current_task_id": None,
            },
        )

        status = request_json(args.base_url, "/api/v1/agents/status")
    except urllib.error.URLError as exc:
        print(f"Runtime verification failed: {exc}", file=sys.stderr)
        return 1

    print(json.dumps({"created": created, "heartbeat": heartbeat, "status": status}, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
