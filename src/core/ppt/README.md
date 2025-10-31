# 深度研究平台PPT生成模块

这个模块实现了基于AI的PPT自动生成功能，支持多种LLM提供商和灵活的渲染选项。

## 功能特性

### 🤖 多LLM支持
- **DeepSeek**: 支持chat和reasoner模型
- **Ollama**: 本地模型支持
- **国内厂商**: 阿里云、百度、腾讯、讯飞（待实现）

### 🎨 多种布局类型
- **TITLE**: 标题页
- **BULLETS**: 项目符号列表
- **COLUMNS**: 多列布局
- **IMAGE**: 图像页面
- **ICONS**: 图标化内容
- **TIMELINE**: 时间线展示
- **CHART**: 数据可视化

### 🖼️ 智能图像集成
- Unsplash API集成
- Pexels API集成
- 占位符图像支持
- 智能缓存机制

## 安装和配置

### 1. 安装依赖
```bash
pip install -r requirements.txt
```

### 2. 环境配置
复制 `.env.example` 为 `.env` 并配置必要的API密钥：

```bash
cp .env.example .env
```

主要配置项：
- `DEEPSEEK_API_KEY`: DeepSeek API密钥
- `OLLAMA_HOST`: Ollama服务地址
- `UNSPLASH_ACCESS_KEY`: Unsplash访问密钥（可选）

### 3. 基本使用

```python
from src.core.ppt.generator import create_presentation

# 创建PPT
params = {
    "title": "AI技术发展趋势",
    "topic": "人工智能技术",
    "n_slides": 10,
    "language": "Chinese",
    "tone": "professional"
}

result = await create_presentation(params)
print(f"PPT已生成: {result['path']}")
```

## 架构设计

### 分层架构
```
src/core/ppt/
├── adapters/          # LLM适配器层
│   ├── deepseek_adapter.py
│   ├── ollama_adapter.py
│   └── domestic_adapter.py
├── generator.py       # 核心生成器
├── renderer.py        # PPTX渲染器
├── image_service.py   # 图像服务
├── prompt_builder.py  # Prompt构建器
├── config.py         # 配置管理
└── utils/            # 工具类
    └── dsl_validator.py
```

### 设计原则
- **分层架构**: 严格遵循API → Service → DAO分层
- **异步优先**: 所有IO操作使用async/await
- **类型安全**: 完整的类型提示
- **错误处理**: 完善的异常处理机制
- **可扩展性**: 模块化设计，易于扩展

## 测试

### 运行所有测试
```bash
pytest tests/ -v
```

### 运行特定测试
```bash
# 单元测试
pytest tests/test_generator.py -v

# 集成测试
pytest tests/test_renderer.py::TestRendererIntegration -v

# 适配器测试
pytest tests/test_adapters.py -v
```

### 测试覆盖率
```bash
pytest --cov=src tests/ --cov-report=html
```

## 开发指南

### 代码规范
- 使用 `black` 进行代码格式化
- 使用 `isort` 进行导入排序
- 使用 `mypy` 进行类型检查
- 使用 `flake8` 进行代码检查

### 添加新的LLM适配器
1. 在 `adapters/` 目录下创建新的适配器文件
2. 实现必要的接口方法
3. 在 `__init__.py` 中导出
4. 添加相应的测试

### 添加新的布局类型
1. 在 `renderer.py` 的 `_parse_section` 中添加解析逻辑
2. 实现对应的渲染方法 `_render_<layout>_slide`
3. 更新 `supported_layouts` 列表
4. 更新模板文件和测试

## 性能优化

### 缓存策略
- 图像URL缓存
- DSL解析结果缓存
- 配置文件缓存

### 并发控制
- 支持并发API请求
- 请求队列管理
- 超时控制

### 监控和日志
- 结构化日志记录
- 性能指标追踪
- 错误统计

## 故障排除

### 常见问题

**Q: PPT生成失败，提示"所有provider都失败"**
A: 检查API密钥配置，确保至少一个provider可用

**Q: Ollama连接失败**
A: 确保Ollama服务正在运行，检查 `OLLAMA_HOST` 配置

**Q: 图像无法加载**
A: 检查图像API密钥配置，或使用占位符图像

### 调试模式
设置环境变量启用详细日志：
```bash
export LOG_LEVEL=DEBUG
```

## 贡献指南

1. Fork 项目
2. 创建功能分支
3. 提交更改
4. 推送到分支
5. 创建 Pull Request

## 许可证

MIT License - 详见 LICENSE 文件

## 更新日志

### v0.1.0 (当前版本)
- 初始版本发布
- 基础PPT生成功能
- DeepSeek和Ollama支持
- 基础布局类型支持
- 图像服务集成