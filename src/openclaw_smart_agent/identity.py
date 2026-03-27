from dataclasses import dataclass
from pathlib import Path

import yaml

from openclaw_smart_agent.config import IdentityDefaults
from openclaw_smart_agent.models import AgentProfile


@dataclass(slots=True)
class IdentityTemplate:
    role: str
    keywords: list[str]
    skills: list[str]
    tools: list[str]
    system_prompt: str
    resource_weight: float

    @classmethod
    def from_dict(cls, payload: dict) -> "IdentityTemplate":
        return cls(
            role=payload["role"],
            keywords=list(payload.get("keywords", [])),
            skills=list(payload.get("skills", [])),
            tools=list(payload.get("tools", ["shell"])),
            system_prompt=payload.get("system_prompt", ""),
            resource_weight=float(payload.get("resource_weight", 0.5)),
        )


class IdentityEnhancer:
    def __init__(
        self,
        template_dir: str | Path | None = None,
        defaults: IdentityDefaults | None = None,
        ai_enhancement_enabled: bool = False,
        llm_enhancer=None,
    ) -> None:
        self.template_dir = Path(template_dir) if template_dir else None
        self.defaults = defaults or IdentityDefaults()
        self.ai_enhancement_enabled = ai_enhancement_enabled
        self.llm_enhancer = llm_enhancer

    def enhance(self, identity: str) -> AgentProfile:
        template = self._match_template(identity)
        if template:
            return AgentProfile(
                identity=identity,
                role=template.role,
                skills=template.skills,
                tools=template.tools,
                system_prompt=template.system_prompt,
                resource_weight=template.resource_weight,
            )

        profile = AgentProfile(
            identity=identity,
            role=self.defaults.role,
            skills=list(self.defaults.skills),
            tools=list(self.defaults.tools),
            system_prompt=self.defaults.system_prompt,
            resource_weight=self.defaults.resource_weight,
        )

        if self.ai_enhancement_enabled and self.llm_enhancer:
            try:
                return self.llm_enhancer(identity, profile)
            except Exception:
                return profile

        return profile

    def _match_template(self, identity: str) -> IdentityTemplate | None:
        normalized_identity = identity.casefold()
        for template in self._load_templates():
            if any(keyword.casefold() in normalized_identity for keyword in template.keywords):
                return template
        return None

    def _load_templates(self) -> list[IdentityTemplate]:
        if not self.template_dir or not self.template_dir.exists():
            return []

        templates: list[IdentityTemplate] = []
        for template_file in sorted(self.template_dir.glob("*.yaml")):
            payload = yaml.safe_load(template_file.read_text(encoding="utf-8")) or {}
            templates.append(IdentityTemplate.from_dict(payload))
        return templates
