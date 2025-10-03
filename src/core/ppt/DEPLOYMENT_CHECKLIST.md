# PPT生成模块部署检查清单

## 📋 部署前检查

### 1. 环境准备

#### Python环境
- [ ] Python 3.8+ 已安装
- [ ] 虚拟环境已创建并激活
- [ ] 所有依赖已安装：`pip install -r requirements.txt`

#### 必需依赖验证
```bash
python -c "import pptx; print('python-pptx: OK')"
python -c "import jinja2; print('jinja2: OK')"
python -c "import aiohttp; print('aiohttp: OK')"
python -c "import yaml; print('pyyaml: OK')"
```

### 2. 配置文件

#### conf.yaml
- [ ] 文件存在于项目根目录
- [ ] PROVIDER_PRIORITY 已配置
- [ ] WORKFLOWS.ppt 已配置
- [ ] 超时和性能参数已设置

#### 环境变量
- [ ] `.env` 文件已创建
- [ ] DEEPSEEK_API_KEY 已设置（如使用DeepSeek）
- [ ] OLLAMA_HOST 已设置（如使用Ollama）
- [ ] 国内厂商密钥已设置（如使用）

### 3. 服务依赖

#### Ollama（如使用本地模型）
- [ ] Ollama服务已安装
- [ ] Ollama服务正在运行：`curl http://localhost:11434/api/tags`
- [ ] 所需模型已下载：`ollama list`
- [ ] 推荐模型：llama3.2:3b, qwen3:32b

#### DeepSeek（如使用云端API）
- [ ] API密钥有效
- [ ] 账户余额充足
- [ ] 网络连接正常
- [ ] 可以访问 https://api.deepseek.com

### 4. 目录结构

- [ ] `./output_reports/ppt/` 目录已创建
- [ ] 目录权限正确（可写）
- [ ] `./data/image_cache/` 目录已创建
- [ ] `./logs/` 目录已创建

```bash
mkdir -p ./output_reports/ppt
mkdir -p ./data/image_cache
mkdir -p ./logs
chmod 755 ./output_reports/ppt
```

### 5. 代码完整性

#### 核心文件
- [ ] `src/core/ppt/__init__.py`
- [ ] `src/core/ppt/config.py`
- [ ] `src/core/ppt/generator.py`
- [ ] `src/core/ppt/renderer.py`
- [ ] `src/core/ppt/prompt_builder.py`
- [ ] `src/core/ppt/image_service.py`

#### 适配器
- [ ] `src/core/ppt/adapters/deepseek_adapter.py`
- [ ] `src/core/ppt/adapters/ollama_adapter.py`
- [ ] `src/core/ppt/adapters/domestic_adapter.py`

#### API
- [ ] `src/core/ppt/api/routes.py`
- [ ] API路由已在 `app.py` 中注册

#### 模板
- [ ] `src/core/ppt/templates/slides_template.xml.j2`

#### 工具
- [ ] `src/core/ppt/utils/dsl_validator.py`

---

## 🧪 功能测试

### 1. 单元测试

```bash
# 运行所有测试
pytest src/core/ppt/tests/ -v

# 运行特定测试
pytest src/core/ppt/tests/test_generator.py -v
```

测试项目：
- [ ] 配置加载测试通过
- [ ] Prompt构建测试通过
- [ ] DSL验证测试通过
- [ ] 大纲生成测试通过

### 2. 适配器测试

#### DeepSeek适配器
```python
import asyncio
from src.core.ppt.adapters.deepseek_adapter import DeepSeekAdapter

async def test():
    adapter = DeepSeekAdapter()
    health = await adapter.health_check()
    print(f"DeepSeek健康状态: {health}")

asyncio.run(test())
```
- [ ] 健康检查通过
- [ ] 生成测试通过

#### Ollama适配器
```python
import asyncio
from src.core.ppt.adapters.ollama_adapter import OllamaAdapter

async def test():
    adapter = OllamaAdapter()
    health = await adapter.health_check()
    print(f"Ollama健康状态: {health}")
    models = await adapter.list_models()
    print(f"可用模型: {[m['name'] for m in models]}")

asyncio.run(test())
```
- [ ] 健康检查通过
- [ ] 模型列表获取成功
- [ ] 生成测试通过

### 3. 端到端测试

```python
import asyncio
from src.core.ppt import create_presentation

async def test():
    result = await create_presentation({
        "title": "测试演示文稿",
        "outline": ["第一页", "第二页", "第三页"],
        "n_slides": 3,
        "language": "Chinese"
    })
    print(f"生成成功: {result['path']}")

asyncio.run(test())
```
- [ ] PPT生成成功
- [ ] 文件存在且可打开
- [ ] 内容符合预期

### 4. API测试

#### 健康检查
```bash
curl http://localhost:8000/api/v1/ppt/health
```
- [ ] 返回200状态码
- [ ] Provider状态正常

#### 创建PPT
```bash
curl -X POST http://localhost:8000/api/v1/ppt/presentation/create \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "title": "API测试",
    "outline": ["测试1", "测试2"],
    "n_slides": 3
  }'
```
- [ ] 返回200状态码
- [ ] 返回presentation_id
- [ ] 返回文件路径
- [ ] 文件已生成

---

## 🚀 部署步骤

### 开发环境

1. **安装依赖**
```bash
pip install -r requirements.txt
```

2. **配置环境变量**
```bash
cp .env.example .env
# 编辑.env文件，填入API密钥
```

3. **启动Ollama（可选）**
```bash
ollama serve
```

4. **启动应用**
```bash
python app.py
```

5. **验证部署**
```bash
curl http://localhost:8000/api/v1/ppt/health
```

### 生产环境

1. **使用Gunicorn**
```bash
gunicorn app:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --timeout 300 \
  --access-logfile logs/access.log \
  --error-logfile logs/error.log
```

2. **使用Docker（推荐）**
```dockerfile
FROM python:3.10-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000
CMD ["gunicorn", "app:app", "--workers", "4", "--worker-class", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000"]
```

3. **使用Systemd服务**
```ini
[Unit]
Description=Deep Research PPT Service
After=network.target

[Service]
Type=notify
User=www-data
WorkingDirectory=/opt/deep-research
Environment="PATH=/opt/deep-research/venv/bin"
ExecStart=/opt/deep-research/venv/bin/gunicorn app:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
Restart=always

[Install]
WantedBy=multi-user.target
```

---

## 📊 监控配置

### 1. 日志监控

- [ ] 日志文件路径配置正确
- [ ] 日志轮转已配置
- [ ] 错误日志告警已设置

### 2. 性能监控

- [ ] 请求延迟监控
- [ ] Provider响应时间监控
- [ ] 成功率监控
- [ ] 错误率监控

### 3. 成本监控

- [ ] API调用次数统计
- [ ] Token使用量统计
- [ ] 成本估算准确
- [ ] 预算告警已设置

---

## 🔒 安全检查

### 1. 密钥管理

- [ ] API密钥不在代码中硬编码
- [ ] 环境变量正确设置
- [ ] `.env` 文件在 `.gitignore` 中
- [ ] 生产环境使用密钥管理服务

### 2. 访问控制

- [ ] JWT认证已启用
- [ ] 用户权限检查正常
- [ ] 配额限制已配置
- [ ] Rate limiting已启用

### 3. 输入验证

- [ ] 参数范围验证
- [ ] 文件类型验证
- [ ] 内容安全过滤
- [ ] SQL注入防护

### 4. 数据隐私

- [ ] 敏感信息脱敏
- [ ] 用户数据隔离
- [ ] 符合GDPR/CCPA
- [ ] 数据加密传输

---

## 📈 性能优化

### 1. 缓存配置

- [ ] Redis缓存已启用
- [ ] 缓存TTL合理设置
- [ ] 缓存命中率监控

### 2. 并发控制

- [ ] 最大并发数已设置
- [ ] 请求队列已配置
- [ ] 超时时间合理

### 3. 资源优化

- [ ] 内存使用监控
- [ ] CPU使用监控
- [ ] 磁盘空间监控
- [ ] 网络带宽监控

---

## 🐛 故障排查

### 常见问题检查

1. **DeepSeek连接失败**
   - [ ] API密钥正确
   - [ ] 网络连接正常
   - [ ] 账户余额充足
   - [ ] API限流检查

2. **Ollama服务不可用**
   - [ ] Ollama服务运行中
   - [ ] 端口11434可访问
   - [ ] 模型已下载
   - [ ] 内存充足

3. **PPT生成失败**
   - [ ] 日志文件检查
   - [ ] Provider状态检查
   - [ ] 磁盘空间充足
   - [ ] 权限正确

4. **性能问题**
   - [ ] 并发数合理
   - [ ] 缓存正常工作
   - [ ] 资源使用正常
   - [ ] 网络延迟检查

---

## 📝 文档检查

- [ ] README.md 完整
- [ ] USAGE_EXAMPLES.md 准确
- [ ] IMPLEMENTATION_SUMMARY.md 最新
- [ ] API文档已生成
- [ ] 部署文档已更新

---

## ✅ 最终验收

### 功能验收
- [ ] 可以使用大纲生成PPT
- [ ] 可以使用主题生成PPT
- [ ] 支持中英文
- [ ] 支持多种语气
- [ ] Provider自动切换正常
- [ ] 错误处理正确

### 性能验收
- [ ] 10页PPT生成时间 < 30秒
- [ ] 并发10个请求正常
- [ ] 内存使用 < 2GB
- [ ] CPU使用 < 80%

### 稳定性验收
- [ ] 连续运行24小时无崩溃
- [ ] 错误率 < 1%
- [ ] 自动恢复正常
- [ ] 日志完整

---

## 📞 支持联系

如遇到问题，请联系：
- 技术支持：support@example.com
- GitHub Issues：https://github.com/your-repo/issues
- 文档：https://docs.example.com

---

**检查日期**: _____________  
**检查人**: _____________  
**部署环境**: [ ] 开发 [ ] 测试 [ ] 生产  
**状态**: [ ] 通过 [ ] 未通过  
**备注**: _____________
