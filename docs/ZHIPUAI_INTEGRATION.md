# ZhipuAI (智谱AI) Integration Guide

## Overview

This document describes the integration of ZhipuAI (智谱AI) into the Deep Research Platform. ZhipuAI provides powerful GLM models with advanced reasoning, web search, and vision capabilities.

## Supported Models

### Text Models
- **GLM-4.6**: Flagship model with 200K context window and 128K max output
- **GLM-4.5**: High-performance model with 128K context window and 96K max output
- **GLM-4.5-Air**: Cost-effective model with 128K context window and 96K max output
- **GLM-4.5-Flash**: Free model with 128K context window and 16K max output

### Vision Model
- **GLM-4.1V-Thinking-Flash**: Free vision model with 64K context window and 16K max output

## Key Features

### 1. Web Search Integration
- Built-in web search with multiple engines
- Support for search_pro, search_std, search_pro_sogou, search_pro_quark
- Intelligent search result processing

### 2. Function Calling
- Advanced function calling capabilities
- JSON schema validation
- Tool integration support

### 3. Vision Processing
- Multi-modal reasoning capabilities
- Image understanding and analysis
- Document processing support

## Configuration

### Environment Variables
Add the following to your `.env` file:

```bash
# ZhipuAI Configuration
ZHIPUAI_API_KEY=your_zhipuai_api_key_here
```

### Configuration File
The following settings are available in `conf.yaml`:

```yaml
# ZhipuAI Configuration
ZHIPUAI_BASE_URL: "https://open.bigmodel.cn/api/paas/v4"
ZHIPUAI_ENABLE_VISION: true

# Model Mapping
ZHIPUAI_MODELS:
  chat: "glm-4.5-flash"                    # Default chat model (free)
  reasoning: "glm-4.6"                     # Reasoning model (flagship)
  vision: "glm-4.1v-thinking-flash"        # Vision model (free)
  search: "glm-4.5-flash"                  # Search model (free)

# Search Engine Configuration
ZHIPUAI_SEARCH_ENGINES:
  search_std: "基础版（智谱AI自研）"        # Basic version
  search_pro: "高级版（智谱AI自研）"        # Advanced version
  search_pro_sogou: "搜狗"                  # Sogou search
  search_pro_quark: "夸克"                  # Quark search

ZHIPUAI_DEFAULT_SEARCH_ENGINE: "search_pro"
ZHIPUAI_MAX_SEARCH_RESULTS: 10
```

## Usage Examples

### Basic Chat
```python
from src.llms.providers.zhipuai_llm import ZhipuAIProvider

provider = ZhipuAIProvider(
    model_name="glm-4.5-flash",
    api_key="your_api_key"
)

messages = [{"role": "user", "content": "你好，请介绍一下你自己"}]
response = await provider.generate(messages)
print(response.content)
```

### Web Search
```python
# With web search
search_config = {
    "search_engine": "search_pro",
    "count": "5",
    "content_size": "medium"
}

response = await provider.generate_with_web_search(
    messages=[{"role": "user", "content": "搜索2025年AI发展趋势"}],
    search_config=search_config
)
```

### Function Calling
```python
tools = [{
    "type": "function",
    "function": {
        "name": "get_weather",
        "description": "Get weather information",
        "parameters": {
            "type": "object",
            "properties": {
                "city": {"type": "string", "description": "City name"}
            },
            "required": ["city"]
        }
    }
}]

response = await provider.generate(
    messages=[{"role": "user", "content": "What's the weather in Beijing?"}],
    tools=tools
)
```

## Testing

Run the ZhipuAI integration tests:

```bash
python test/test_zhipuai.py
```

The test suite includes:
- Health check
- Model capabilities verification
- Basic generation testing
- Function calling
- Web search functionality
- Vision processing (if supported)

## Smart Routing

ZhipuAI models are integrated into the smart routing system:

```python
# Research tasks will prioritize ZhipuAI for its search capabilities
router = SmartModelRouter(config)
response = await router.route_and_chat_auto(
    task_type="research",
    messages=[{"role": "user", "content": "Research latest AI trends"}]
)
```

### Provider Priority Configuration
```yaml
PROVIDER_PRIORITY:
  research: ["zhipuai", "deepseek", "kimi", "ollama"]
  reasoning: ["zhipuai", "deepseek", "ollama"]
  vision: ["zhipuai", "doubao", "ollama"]
  code: ["zhipuai", "deepseek", "ollama"]
```

## API Rate Limits

- **GLM-4.6**: Premium model with higher rate limits
- **GLM-4.5**: High-performance model with standard limits
- **GLM-4.5-Air**: Cost-effective model with moderate limits
- **GLM-4.5-Flash**: Free model with generous limits
- **GLM-4.1V-Thinking-Flash**: Free vision model

## Cost Optimization

- Use `glm-4.5-flash` for cost-effective chat and search
- Use `glm-4.6` for complex reasoning tasks
- Use `glm-4.1v-thinking-flash` for vision processing
- Leverage built-in web search to reduce external API calls

## Troubleshooting

### Common Issues

1. **API Key Not Found**
   ```
   ❌ 错误: 未在 .env 文件中找到 'ZHIPUAI_API_KEY'
   ```
   **Solution**: Add `ZHIPUAI_API_KEY=your_key` to `.env` file

2. **Model Not Available**
   ```
   ❌ 模型不可用: glm-4.6
   ```
   **Solution**: Check your account permissions and available models

3. **Rate Limit Exceeded**
   ```
   ❌ 请求频率超限
   ```
   **Solution**: Implement rate limiting or use free models

### Getting API Key

1. Visit [ZhipuAI Console](https://open.bigmodel.cn/)
2. Register and verify your account
3. Navigate to API Keys section
4. Create new API key
5. Add to `.env` file as `ZHIPUAI_API_KEY=your_key`

## Best Practices

1. **Model Selection**: Choose appropriate models based on task complexity
2. **Cost Management**: Use free models for development and testing
3. **Error Handling**: Implement proper error handling for API failures
4. **Rate Limiting**: Respect API rate limits to avoid service interruption
5. **Security**: Store API keys securely using environment variables

## Integration with Existing Features

### RAG and Vector Search
ZhipuAI models work seamlessly with the existing RAG system for enhanced document understanding.

### Agent Workflows
ZhipuAI models can be used in LangGraph-based agent workflows for complex multi-step tasks.

### Document Processing
Vision models support document analysis, OCR, and multi-modal content extraction.

## Future Enhancements

- Support for image generation models (CogView-3-Flash)
- Video generation capabilities (CogVideoX-Flash)
- Enhanced search filters and domain-specific search
- Custom model fine-tuning support