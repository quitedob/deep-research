import pytest
from backend.core.llm.factory import LLMFactory
from backend.config.llm_config import get_config


@pytest.mark.live
async def test_zhipu_provider_returns_text():
    config = get_config().get_provider_config("zhipu")
    llm = LLMFactory.create_llm("zhipu")
    try:
        response = await llm.chat_completion(model=config.default_model,
            messages=[{"role": "user", "content": "Reply with a short greeting."}], max_tokens=100)
        assert response["choices"][0]["message"]["content"].strip()
    finally:
        await llm.close()
