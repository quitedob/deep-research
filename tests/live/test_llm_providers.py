import pytest
from backend.config.llm_config import get_config
from backend.core.llm.factory import LLMFactory


@pytest.mark.live
async def test_default_deepseek_provider_returns_text():
    config = get_config().get_provider_config("deepseek")
    llm = LLMFactory.create_llm("deepseek")
    try:
        response = await llm.chat_completion(model=config.default_model,
            messages=[{"role": "user", "content": "Reply with a short greeting."}], max_tokens=100)
        assert response["choices"][0]["message"]["content"].strip()
    finally:
        await llm.close()
