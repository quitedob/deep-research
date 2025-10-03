# PPT生成模块快速开始指南

## 🚀 5分钟快速上手

### 步骤1: 安装依赖（1分钟）

```bash
# 确保已安装Python 3.8+
python --version

# 安装依赖
pip install python-pptx jinja2 aiohttp pyyaml
```

### 步骤2: 配置环境变量（1分钟）

创建 `.env` 文件或设置环境变量：

```bash
# 选项A: 使用DeepSeek（云端，需要API密钥）
export DEEPSEEK_API_KEY="your_api_key_here"

# 选项B: 使用Ollama（本地，免费）
export OLLAMA_HOST="http://localhost:11434"

# 如果使用Ollama，先启动服务
ollama serve
```

### 步骤3: 生成你的第一个PPT（3分钟）

创建文件 `test_ppt.py`：

```python
import asyncio
from src.core.ppt import create_presentation

async def main():
    # 定义PPT参数
    params = {
        "title": "我的第一个AI生成PPT",
        "outline": [
            "欢迎页",
            "项目介绍",
            "核心功能",
            "技术架构",
            "总结"
        ],
        "n_slides": 5,
        "language": "Chinese",
        "tone": "professional"
    }
    
    # 生成PPT
    print("正在生成PPT，请稍候...")
    result = await create_presentation(params)
    
    # 输出结果
    print(f"✅ PPT生成成功！")
    print(f"📁 文件路径: {result['path']}")
    print(f"🆔 演示文稿ID: {result['presentation_id']}")

# 运行
if __name__ == "__main__":
    asyncio.run(main())
```

运行：
```bash
python test_ppt.py
```

---

## 🎯 常用场景

### 场景1: 快速生成工作汇报PPT

```python
params = {
    "title": "2025年第一季度工作汇报",
    "outline": [
        "工作概述",
        "主要成果",
        "数据分析",
        "遇到的挑战",
        "下季度计划"
    ],
    "n_slides": 8,
    "language": "Chinese",
    "tone": "professional"
}
```

### 场景2: 生成技术分享PPT

```python
params = {
    "title": "深度学习入门",
    "topic": "深度学习",  # 自动生成大纲
    "n_slides": 12,
    "language": "Chinese",
    "tone": "casual"
}
```

### 场景3: 生成英文演示文稿

```python
params = {
    "title": "Introduction to Machine Learning",
    "outline": [
        "What is ML",
        "Types of ML",
        "Algorithms",
        "Applications",
        "Future Trends"
    ],
    "n_slides": 10,
    "language": "English",
    "tone": "professional"
}
```

---

## 🔧 使用API

### 启动服务

```bash
# 开发模式
python app.py

# 生产模式
gunicorn app:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### 调用API

```bash
# 获取访问令牌（如果需要）
TOKEN="your_access_token"

# 创建PPT
curl -X POST http://localhost:8000/api/v1/ppt/presentation/create \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "title": "API测试PPT",
    "outline": ["第一页", "第二页", "第三页"],
    "n_slides": 3,
    "language": "Chinese"
  }'

# 健康检查
curl http://localhost:8000/api/v1/ppt/health
```

---

## 💡 实用技巧

### 技巧1: 使用主题自动生成大纲

不知道写什么？让AI帮你生成大纲：

```python
params = {
    "title": "人工智能的未来",
    "topic": "人工智能",  # 只需提供主题
    "n_slides": 10,
    "language": "Chinese"
}
```

### 技巧2: 调整语气风格

根据场合选择合适的语气：

```python
# 正式场合
tone = "professional"

# 轻松场合
tone = "casual"

# 创意展示
tone = "creative"
```

### 技巧3: 控制幻灯片数量

```python
# 快速概览（3-5页）
n_slides = 5

# 标准演示（8-12页）
n_slides = 10

# 详细讲解（15-20页）
n_slides = 20
```

### 技巧4: 本地优先，降低成本

在 `conf.yaml` 中配置：

```yaml
PROVIDER_PRIORITY:
  ppt_content: ["ollama", "deepseek"]  # 优先使用本地Ollama
```

---

## 🐛 常见问题快速解决

### 问题1: "DeepSeek API调用失败"

**解决方案：**
```bash
# 检查API密钥
echo $DEEPSEEK_API_KEY

# 如果没有，设置它
export DEEPSEEK_API_KEY="your_key"

# 或者切换到Ollama
export OLLAMA_HOST="http://localhost:11434"
```

### 问题2: "Ollama服务不可用"

**解决方案：**
```bash
# 启动Ollama
ollama serve

# 下载模型
ollama pull llama3.2:3b

# 验证
curl http://localhost:11434/api/tags
```

### 问题3: "生成的PPT打不开"

**解决方案：**
```bash
# 检查文件是否存在
ls -lh ./output_reports/ppt/

# 检查权限
chmod 644 ./output_reports/ppt/*.pptx

# 使用最新版本的PowerPoint或WPS打开
```

### 问题4: "生成速度太慢"

**解决方案：**
1. 使用更快的模型（gemma3:4b）
2. 减少幻灯片数量
3. 启用缓存
4. 使用本地Ollama而非云端API

---

## 📚 下一步

### 学习更多

- 📖 [完整文档](./README.md)
- 💻 [使用示例](./USAGE_EXAMPLES.md)
- 🔧 [实现细节](./IMPLEMENTATION_SUMMARY.md)
- ✅ [部署检查清单](./DEPLOYMENT_CHECKLIST.md)

### 进阶功能

1. **自定义模板**
   - 修改 `templates/slides_template.xml.j2`
   - 添加自己的布局样式

2. **集成RAG**
   - 上传文档增强内容
   - 使用知识库生成PPT

3. **批量生成**
   - 编写脚本批量处理
   - 使用任务队列

4. **API集成**
   - 集成到现有系统
   - 构建前端界面

---

## 🎉 成功案例

### 案例1: 10分钟完成季度汇报

```python
# 某公司使用本模块，从数据到PPT只需10分钟
params = {
    "title": "Q1销售业绩汇报",
    "outline": [
        "业绩总览",
        "区域分析",
        "产品表现",
        "客户反馈",
        "改进措施",
        "Q2目标"
    ],
    "n_slides": 12,
    "language": "Chinese"
}
```

### 案例2: 技术分享会准备

```python
# 工程师快速准备技术分享
params = {
    "title": "微服务架构实践",
    "topic": "微服务",
    "n_slides": 15,
    "language": "Chinese",
    "tone": "casual"
}
```

### 案例3: 教学课件制作

```python
# 老师制作教学PPT
params = {
    "title": "Python编程基础",
    "outline": [
        "Python简介",
        "变量和数据类型",
        "控制流程",
        "函数",
        "面向对象",
        "实战项目"
    ],
    "n_slides": 20,
    "language": "Chinese",
    "tone": "professional"
}
```

---

## 💬 获取帮助

遇到问题？我们来帮你！

1. **查看文档**: 先看看 [README.md](./README.md)
2. **搜索Issues**: 在 [GitHub Issues](https://github.com/your-repo/issues) 搜索
3. **提问**: 创建新的Issue描述你的问题
4. **联系支持**: support@example.com

---

## 🌟 分享你的成功

使用本模块创建了很棒的PPT？

- ⭐ 给项目点个Star
- 📝 分享你的使用案例
- 🐛 报告Bug帮助改进
- 💡 提出新功能建议

---

**祝你使用愉快！🎊**

开始创建你的第一个AI生成PPT吧！
