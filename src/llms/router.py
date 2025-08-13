from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Any
from pathlib import Path
import os
import yaml

from src.llms.providers.ollama_llm import OllamaProvider
from src.llms.providers.deepseek_llm import DeepSeekProvider
from src.llms.providers.kimi_llm import KimiProvider


@dataclass
class LLMMessage:
    role: str
    content: str


class ModelRouter:
    """模型路由器：根据 conf.yaml 的 PROVIDER_PRIORITY 选择合适 Provider。"""

    def __init__(self, conf: Dict[str, Any]):
        self.conf = conf
        self.providers: Dict[str, Any] = {}
        self._init_providers()

    @classmethod
    def from_conf(cls, path: Path) -> "ModelRouter":
        if path.exists():
            conf = yaml.safe_load(path.read_text(encoding="utf-8"))
        else:
            conf = {
                "PROVIDER_PRIORITY": {"general": ["ollama", "deepseek", "kimi"]},
                "OLLAMA_BASE_URL": "http://localhost:11434/v1",
                "DEEPSEEK_BASE_URL": "https://api.deepseek.com/v1",
                "DEEPSEEK_MODELS": {"chat": "deepseek-chat"},
                "KIMI_BASE_URL": os.getenv("MOONSHOT_API_BASE", "https://api.moonshot.ai/v1"),
                "KIMI_MODEL": "moonshot-v1-8k",
            }
        return cls(conf)

    def _init_providers(self) -> None:
        # Ollama（本地）
        self.providers["ollama"] = OllamaProvider(
            model_name=self.conf.get("OLLAMA_SMALL_MODEL", "qwen2.5:7b"),
            base_url=self.conf.get("OLLAMA_BASE_URL", "http://localhost:11434/v1"),
        )

        # DeepSeek（需要 API Key）
        self.providers["deepseek"] = DeepSeekProvider(
            model_name=(self.conf.get("DEEPSEEK_MODELS", {}) or {}).get("chat", "deepseek-chat"),
            api_key=os.getenv("DEEPSEEK_API_KEY", ""),
            base_url=self.conf.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1"),
        )

        # Kimi / Moonshot（需要 API Key）
        self.providers["kimi"] = KimiProvider(
            model_name=self.conf.get("KIMI_MODEL", "moonshot-v1-8k"),
            api_key=os.getenv("MOONSHOT_API_KEY", ""),
            base_url=os.getenv("MOONSHOT_API_BASE", self.conf.get("KIMI_BASE_URL", "https://api.moonshot.ai/v1")),
        )

    async def health(self) -> Dict[str, Any]:
        results: Dict[str, Any] = {}
        for name, provider in self.providers.items():
            try:
                ok, message = await provider.health_check()
            except Exception as e:
                ok, message = False, str(e)
            results[name] = {"ok": ok, "message": message}
        return {"providers": results, "provider_priority": self.conf.get("PROVIDER_PRIORITY", {})}

    def _choose_provider(self, task: str, size: str) -> str:
        priority = (self.conf.get("PROVIDER_PRIORITY", {}).get(task)
                    or self.conf.get("PROVIDER_PRIORITY", {}).get("general")
                    or ["ollama", "deepseek", "kimi"])
        return priority[0]

    async def chat(
        self,
        task: str,
        size: str,
        messages: List[LLMMessage],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> Dict[str, Any]:
        provider_name = self._choose_provider(task, size)
        provider = self.providers[provider_name]
        result = await provider.generate(
            messages=[{"role": m.role, "content": m.content} for m in messages],
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return {"model": result.model, "content": result.content}


