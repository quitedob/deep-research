# PPT生成模块

## 概述

本模块为 deep-research 项目提供AI驱动的PPT生成功能，支持多种LLM提供商（DeepSeek、Ollama、国内厂商），实现从主题到PPTX文件的完整流程。

## 功能特性

- **多模型支持**: DeepSeek（云端）、Ollama（本地）、国内API厂商
- **智能路由**: 根据任务类型和可用性自动选择最佳模型
- **结构化生成**: 使用XML DSL确保PPT结构合理
- **多种布局**: 支持标题页、内容页、图文页等多种布局
- **图像集成**: 支持图像查询和集成（可选）
- **文档增强**: 支持RAG文档上传和内容增强

## 环境变量配置

### DeepSeek配置
```bash
DEEPSEEK_BASE_URL=https://api.deepseek.com/v1
DEEPSEEK_API_KEY=your_api_key_here
```

### Ollama配置
```bash
OLLAMA_HOST=http://localhost:11434
OLLAMA_PPT_MODEL=llama3.2:3b
```

### 国内厂商配置（可选）
```bash
# 阿里云
ALIYUN_API_KEY=your_key
ALIYUN_MODEL=qwen-plus

# 百度
BAIDU_API_KEY=your_key
BAIDU_SECRET_KEY=your_secret
```

## 快速开始

### 1. 安装依赖

确保已安装所需依赖：
```bash
pip install python-pptx pillow requests aiohttp jinja2
```

### 2. 基本使用

```python
from src.core.ppt.generator import create_presentation

# 创建PPT
result = await create_presentation({
    "title": "AI技术发展趋势",
    "outline": ["AI概述", "技术突破", "应用场景", "未来展望"],
    "n_slides": 10,
    "language": "Chinese",
    "tone": "professional"
})

print(f"PPT已生成: {result['path']}")
```

### 3. API调用示例

```bash
curl -X POST http://localhost:8000/api/v1/ppt/presentation/create \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "title": "AI技术发展趋势",
    "outline": ["AI概述", "技术突破", "应用场景", "未来展望"],
    "n_slides": 10,
    "language": "Chinese"
  }'
```

## 模块结构

```
src/core/ppt/
├── README.md                    # 本文件
├── config.py                    # 配置管理
├── adapters/                    # LLM适配器
│   ├── __init__.py
│   ├── deepseek_adapter.py     # DeepSeek适配器
│   ├── ollama_adapter.py       # Ollama适配器
│   └── domestic_adapter.py     # 国内厂商适配器
├── templates/                   # Prompt模板
│   └── slides_template.xml.j2  # XML DSL模板
├── prompt_builder.py           # Prompt构建器
├── generator.py                # 主生成流程
├── renderer.py                 # PPTX渲染器
├── image_service.py            # 图像服务
├── api/                        # API路由
│   └── routes.py               # FastAPI路由
├── tests/                      # 测试文件
│   └── test_generator.py
└── utils/                      # 工具函数
    └── dsl_validator.py        # DSL验证器
```

## Provider优先级配置

在 `conf.yaml` 中配置：

```yaml
PROVIDER_PRIORITY:
  ppt_outline: ["deepseek", "ollama"]      # 大纲生成优先DeepSeek
  ppt_content: ["deepseek", "ollama"]      # 内容生成优先DeepSeek
  ppt_simple: ["ollama", "deepseek"]       # 简单任务优先本地
```

## 支持的布局类型

- **TITLE**: 标题页
- **BULLETS**: 项目符号列表
- **COLUMNS**: 多列布局
- **IMAGE**: 图文混排
- **ICONS**: 图标展示
- **TIMELINE**: 时间线
- **CHART**: 图表（占位符）

## 成本估算

- **DeepSeek**: 约 ¥0.002-0.003 / 千tokens
- **Ollama**: 本地运行，无API费用
- **国内厂商**: 根据具体厂商定价

## 性能指标

- **生成速度**: 10-20秒/PPT（10页）
- **并发支持**: 最多10个并发请求
- **缓存**: 支持结果缓存（30分钟）

## 故障排查

### 1. DeepSeek连接失败
- 检查API密钥是否正确
- 确认网络连接正常
- 查看余额是否充足

### 2. Ollama服务不可用
- 确认Ollama服务已启动：`ollama serve`
- 检查模型是否已下载：`ollama list`
- 验证端口是否正确（默认11434）

### 3. 生成内容质量问题
- 调整temperature参数（0.7-1.3）
- 优化prompt模板
- 使用更强大的模型

## 开发指南

### 添加新的Provider

1. 在 `adapters/` 下创建新适配器
2. 实现 `generate()` 和 `health_check()` 方法
3. 在 `config.py` 中注册
4. 更新 `PROVIDER_PRIORITY` 配置

### 自定义布局

1. 在 `templates/slides_template.xml.j2` 中定义新布局
2. 在 `renderer.py` 中实现渲染逻辑
3. 更新文档说明

## 许可证

本模块遵循项目主许可证。

## 联系方式

如有问题或建议，请提交Issue或Pull Request。
