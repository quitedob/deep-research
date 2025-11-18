文本模型是一类专注于处理和生成自然语言的模型，涵盖了语言理解与推理能力，能够自动处理海量文本数据并进行逻辑推导。智谱的文本模型结合了强大的语言模型和推理模型，使得系统不仅能理解和生成文本内容，还能进行高层次的推理和判断。
模型	定位	特点	上下文	最大输出
GLM-4.6	高智能旗舰	- 最强性能
- 高级编码能力、强大推理
以及工具调用能力	200K	128K
GLM-4.5	超强性能	- 性能优秀
- 强大的推理能力、代码生成能力
以及工具调用能力	128K	96K
GLM-4.5-Air	高性价比	- 同参数规模性能最佳
- 在推理、编码和智能体任务上表现
强劲	128K	96K
GLM-4.5-Flash	免费模型	- 最新基座模型的普惠版本	128K	96K
- 多语言支持
- 支持外部工具调用	128K	16K
视觉模型是一类能处理图像或视频等视觉信息的模型，广泛应用于识别、分析与决策任务。其中，视觉理解模型侧重于看懂图像内容，如识别物体、场景和关系；而视觉推理模型进一步具备看图思考的能力，能结合视觉与语言信息完成逻辑判断、因果分析和多步推理，常用于图文问答、图像描述生成、多模态对齐等复杂任务。
模型	定位	特点	上下文	最大输出
GLM-4.1V-Thinking-Flash	免费模型	- 视觉推理能力
- 复杂场景理解
- 多步骤分析	64K	16K
图像生成模型是一类通过学习海量图像数据，实现从文本生成高质量图片的模型，广泛应用于视觉内容创作、游戏美术、产品设计、医学影像合成等领域。
模型	定位	特点	多分辨率
CogView-3-Flash	免费模型	- 创意丰富多样
- 推理速度快	支持
视频生成模型
视频生成模型是一类通过学习时序视觉数据，从文本、图像或其他视频素材生成动态视频内容的模型，广泛应用于影视制作、虚拟人、动画生成、数字营销等领域。
模型	定位	特点	多分辨率
CogVideoX-Flash	免费模型	- 沉浸式AI音效
- 4K 高清画质呈现
- 10 秒视频时长拓展
- 60fps 高帧率输出	图像、文本	支持
Web Search API
Web Search API 是一个专给大模型用的搜索引擎，在传统搜索引擎网页抓取、排序的能力基础上，增强了意图识别能力，返回更适合大模型处理的结果（网页标题、网页 URL、网页摘要、网站名称、网站图标等）。
意图增强检索：支持智能识别用户查询意图，自动判断是否需要网页检索
结构化输出：返回适合 LLM 处理的数据格式（含标题/URL/摘要/网站名/图标等）
多引擎支持：整合智谱自研引擎及主流搜索引擎（搜狗/夸克）
支持指定范围搜索：可自定义返回的搜索结果数量、域名、时间范围等指定搜索，并可调整网页摘要的字数，帮助实现搜索行为的精细化管控
可灵活控制输出结果时间：响应参数可设置网页发布时间字段，便于时效性分析和排序
接口调用
接口文档：Web Search API
场景示例：搜索财经新闻
Python
响应示例
安装 SDK
Copy
# 安装最新版本
pip install zai-sdk
# 或指定版本
pip install zai-sdk==0.0.4
验证安装
Copy
import zai
print(zai.__version__)

from zai import ZhipuAiClient
client = ZhipuAiClient(api_key="your-api-key")

response = client.web_search.web_search(
   search_engine="search_pro",
   search_query="搜索2025年4月的财经新闻",
   count=15,  # 返回结果的条数，范围1-50，默认10
   search_domain_filter="www.sohu.com",  # 只访问指定域名的内容
   search_recency_filter="noLimit",  # 搜索指定日期范围内的内容
   content_size="high"  # 控制网页摘要的字数，默认medium
)
print(response)
MCP Server
访问官方MCP文档了解更多关于该协议的信息。
MCP Server 配置指南
对话中的网络搜索
对话中的网络搜索允许 Completions API 调用搜索引擎，将实时网络检索结果与 GLM 的生成能力相结合，提供最新且可验证的答案。
API文档：对话中的网络搜索
示例：财经分析摘要
Python 响应示例 安装 SDK
# 安装最新版本
pip install zai-sdk

# 或指定版本
pip install zai-sdk==0.0.4
验证安装

import zai
print(zai.__version__)

from zai import ZhipuAiClient

client = ZhipuAiClient(api_key="your-api-key")

# 定义工具参数
tools = [{
    "type": "web_search",
    "web_search": {
        "enable": "True",
        "search_engine": "search_pro",
        "search_result": "True",
        "search_prompt": "你是一位财经分析师。请用简洁的语言总结网络搜索{search_result}中的关键信息，按重要性排序并引用来源日期。今天的日期是2025年4月11日。",
        "count": "5",
        "search_domain_filter": "www.sohu.com",
        "search_recency_filter": "noLimit",
        "content_size": "high"
    }
}]
# 定义用户消息
messages = [{
    "role": "user",
    "content": "2025年4月的重要财经事件、政策变化和市场数据"
}]
# 调用API获取响应
response = client.chat.completions.create(
    model="glm-4-air",  # 模型标识符
    messages=messages,  # 用户消息
    tools=tools         # 工具参数
)
# 打印响应结果
print(response)
搜索智能体
基于搜索意图，智能分解为多个搜索查询，检索对应的搜索结果，并综合所有网页内容生成全面的模型回答。答案详尽且富有洞察力。
API文档: 智能体搜索
使用场景示例: 风险评估报告生成
风险评估报告生成示例
搜索引擎说明
搜索引擎编码	特性	价格
search_std	基础版（智谱AI 自研）：满足日常查询需求，性价比极高	0.01元/次
search_pro	高级版（智谱AI 自研）：多引擎协作显著降低空结果率，召回率和准确率大幅提升	0.03元/次
search_pro_sogou	搜狗：覆盖腾讯生态（新闻/企鹅号）和知乎内容，在百科、医疗等垂直领域权威性强	0.05元/次
search_pro_quark	夸克：精准触达垂直内容	0.05元/次
函数调用

Copy page

智能体函数调用功能详细介绍

函数调用工具允许智能体调用外部函数和 API，极大扩展了 AI 助手的能力边界，使其能够执行具体的操作和获取实时数据。
功能特性 结构化输出 自动解析函数参数 类型验证和转换 错误处理和重试 结果格式化 多函数支持 同时定义多个函数 函数链式调用 条件函数选择 并行函数执行 灵活集成 RESTful API 集成 数据库操作 文件系统访问 第三方服务调用 基础用法 定义函数 API调用 安装SDK

# 安装最新版本
pip install zai-sdk

# 或指定版本
pip install zai-sdk==0.0.4
验证安装

import zai
print(zai.__version__)
定义函数

import json
from zai import ZhipuAiClient

client = ZhipuAiClient(api_key="your_api_key")

# 定义天气查询函数
def get_weather(city: str) -> dict:
    """获取指定城市的天气信息"""
    # 这里应该调用真实的天气 API
    weather_data = {
        "city": city,
        "temperature": "22°C",
        "condition": "晴天",
        "humidity": "65%",
        "wind_speed": "5 km/h"
    }
    return weather_data

# 函数描述格式
tools = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "获取指定城市的当前天气信息",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "城市名称，例如：北京、上海"
                    }
                },
                "required": ["city"]
            }
        }
    }
]