import json
from dataclasses import asdict
import os
from urllib import error, request

from openclaw_smart_agent.config import IdentityConfig
from openclaw_smart_agent.models import AgentProfile


class OpenClawGatewayLLMEnhancer:
    def __init__(self, config: IdentityConfig, transport=None) -> None:
        self.config = config
        self.transport = transport or self._default_transport

    def __call__(self, identity: str, fallback_profile: AgentProfile) -> AgentProfile:
        try:
            response = self.transport(
                self._endpoint_url(),
                self._request_headers(),
                self._request_payload(identity, fallback_profile),
                self.config.timeout_ms / 1000,
            )
            payload = self._extract_json_payload(response)
        except Exception:
            return fallback_profile

        return AgentProfile(
            identity=identity,
            role=self._normalize_role(payload.get("role"), fallback_profile.role),
            skills=self._normalize_list(payload.get("skills"), fallback_profile.skills),
            tools=self._normalize_list(payload.get("tools"), fallback_profile.tools),
            system_prompt=self._normalize_text(
                payload.get("system_prompt"),
                fallback_profile.system_prompt,
            ),
            resource_weight=self._normalize_weight(
                payload.get("resource_weight"),
                fallback_profile.resource_weight,
            ),
        )

    def _endpoint_url(self) -> str:
        return f"{self.config.openclaw_gateway_url.rstrip('/')}/tools/invoke"

    def _request_headers(self) -> dict[str, str]:
        headers = {"content-type": "application/json"}
        bearer_token = (
            self.config.gateway_bearer_token
            or os.getenv("OPENCLAW_GATEWAY_TOKEN")
            or os.getenv("OPENCLAW_GATEWAY_PASSWORD")
        )
        if bearer_token:
            headers["authorization"] = f"Bearer {bearer_token}"
        return headers

    def _request_payload(self, identity: str, fallback_profile: AgentProfile) -> dict:
        args = {
            "prompt": (
                "Generate a concise agent profile for the provided identity. "
                "Return JSON only with role, skills, tools, system_prompt, and resource_weight. "
                "Use a stable lowercase hyphenated role, keep skills/tools short, and choose "
                "resource_weight between 0.1 and 1.0."
            ),
            "input": {
                "identity": identity,
                "fallback_profile": asdict(fallback_profile),
            },
            "schema": {
                "type": "object",
                "properties": {
                    "role": {"type": "string"},
                    "skills": {"type": "array", "items": {"type": "string"}},
                    "tools": {"type": "array", "items": {"type": "string"}},
                    "system_prompt": {"type": "string"},
                    "resource_weight": {"type": "number"},
                },
                "required": ["role", "skills", "tools", "system_prompt", "resource_weight"],
                "additionalProperties": False,
            },
            "thinking": self.config.thinking,
            "maxTokens": self.config.max_tokens,
            "timeoutMs": self.config.timeout_ms,
        }
        if self.config.provider:
            args["provider"] = self.config.provider
        if self.config.model:
            args["model"] = self.config.model
        if self.config.auth_profile_id:
            args["authProfileId"] = self.config.auth_profile_id

        return {
            "tool": "llm-task",
            "action": "json",
            "args": args,
            "sessionKey": self.config.session_key,
        }

    @staticmethod
    def _default_transport(url: str, headers: dict[str, str], payload: dict, timeout_seconds: float) -> dict:
        req = request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST",
        )
        with request.urlopen(req, timeout=timeout_seconds) as response:
            body = json.loads(response.read().decode("utf-8"))
        if not body.get("ok", False):
            message = body.get("error", {}).get("message", "unknown OpenClaw Gateway error")
            raise error.HTTPError(url, 500, message, hdrs=None, fp=None)
        return body

    @staticmethod
    def _extract_json_payload(response_body: dict) -> dict:
        result = response_body.get("result", response_body)
        candidates = [
            result.get("details", {}).get("json") if isinstance(result.get("details"), dict) else None,
            result.get("json"),
            result,
        ]
        for candidate in candidates:
            if isinstance(candidate, dict) and any(
                key in candidate for key in ("role", "skills", "tools", "system_prompt", "resource_weight")
            ):
                return candidate

        if isinstance(result, dict):
            for item in result.get("content", []):
                if item.get("type") != "text":
                    continue
                try:
                    parsed = json.loads(item.get("text", ""))
                except json.JSONDecodeError:
                    continue
                if isinstance(parsed, dict):
                    return parsed

        raise ValueError("OpenClaw llm-task response did not include a usable JSON payload")

    @staticmethod
    def _normalize_role(value: object, fallback: str) -> str:
        if not isinstance(value, str):
            return fallback
        normalized = value.strip()
        return normalized or fallback

    @staticmethod
    def _normalize_text(value: object, fallback: str) -> str:
        if not isinstance(value, str):
            return fallback
        normalized = value.strip()
        return normalized or fallback

    @staticmethod
    def _normalize_list(value: object, fallback: list[str]) -> list[str]:
        if isinstance(value, str):
            items = [value]
        elif isinstance(value, list):
            items = [item for item in value if isinstance(item, str) and item.strip()]
        else:
            return list(fallback)
        return items or list(fallback)

    @staticmethod
    def _normalize_weight(value: object, fallback: float) -> float:
        try:
            weight = float(value)
        except (TypeError, ValueError):
            return fallback
        return min(1.0, max(0.1, weight))
