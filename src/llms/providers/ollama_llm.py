from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from openai import AsyncOpenAI


@dataclass
class _Resp:
    content: str
    model: str


class OllamaProvider:
    """Ollama Provider（OpenAI 兼容 /v1 接口）。"""

    def __init__(self, model_name: str, base_url: str):
        self.model_name = model_name
        # Ollama 允许任意非空 api_key
        self.client = AsyncOpenAI(base_url=base_url, api_key="ollama")

    async def generate(
        self,
        messages: List[Dict[str, Any]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> _Resp:
        resp = await self.client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return _Resp(content=resp.choices[0].message.content, model=self.model_name)

    async def health_check(self):
        try:
            _ = await self.client.models.list()
            return True, "ok"
        except Exception as e:
            return False, str(e)


