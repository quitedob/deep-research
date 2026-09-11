首次调用 API
DeepSeek API 使用与 OpenAI 兼容的 API 格式，通过修改配置，您可以使用 OpenAI SDK 来访问 DeepSeek API，或使用与 OpenAI API 兼容的软件。

PARAM	VALUE
base_url *       	https://api.deepseek.com
api_key	apply for an API key
* 出于与 OpenAI 兼容考虑，您也可以将 base_url 设置为 https://api.deepseek.com/v1 来使用，但注意，此处 v1 与模型版本无关。

* deepseek-chat 和 deepseek-reasoner 都已经升级为 DeepSeek-V3.2-Exp。deepseek-chat 对应 DeepSeek-V3.2-Exp 的非思考模式，deepseek-reasoner 对应 DeepSeek-V3.2-Exp 的思考模式。

* 我们通过额外的接口，临时保留了 V3.1-Terminus 的 API 访问，以供用户进行对比测试，访问方法请参考文档。

调用对话 API
在创建 API key 之后，你可以使用以下样例脚本的来访问 DeepSeek API。样例为非流式输出，您可以将 stream 设置为 true 来使用流式输出。

curl
python
nodejs
curl https://api.deepseek.com/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${DEEPSEEK_API_KEY}" \
  -d '{
        "model": "deepseek-chat",
        "messages": [
          {"role": "system", "content": "You are a helpful assistant."},
          {"role": "user", "content": "Hello!"}
        ],
        "stream": false
      }'
模型 & 价格
下表所列模型价格以“百万 tokens”为单位。Token 是模型用来表示自然语言文本的的最小单位，可以是一个词、一个数字或一个标点符号等。我们将根据模型输入和输出的总 token 数进行计量计费。

模型细节
模型	deepseek-chat	deepseek-reasoner
模型版本(1)	DeepSeek-V3.2-Exp
（非思考模式）	DeepSeek-V3.2-Exp
（思考模式）
上下文长度	128K
输出长度	默认 4K，最大 8K	默认 32K，最大 64K
功能	Json Output	支持	支持
Function Calling	支持	不支持(2)
对话前缀续写（Beta）	支持	支持
FIM 补全（Beta）	支持	不支持
价格	百万tokens输入（缓存命中）	0.2元
百万tokens输入（缓存未命中）	2元
百万tokens输出	3元
(1) 我们通过额外的接口，临时保留了 V3.1-Terminus 的 API 访问，以供用户进行对比测试，访问方法请参考文档。
(2) 如果给 deepseek-reasoner 模型的请求中有 tools 参数，请求实际上将使用 deepseek-chat 模型。
扣费规则
扣减费用 = token 消耗量 × 模型单价，对应的费用将直接从充值余额或赠送余额中进行扣减。 当充值余额与赠送余额同时存在时，优先扣减赠送余额。

产品价格可能发生变动，DeepSeek 保留修改价格的权利。请您依据实际用量按需充值，定期查看此页面以获知最新价格信息。
Temperature 设置
temperature 参数默认为 1.0。

我们建议您根据如下表格，按使用场景设置 temperature。
场景	温度
代码生成/数学解题   	0.0
数据抽取/分析	1.0
通用对话	1.3
翻译	1.3
创意类写作/诗歌创作	1.5
Token 用量计算
token 是模型用来表示自然语言文本的基本单位，也是我们的计费单元，可以直观的理解为“字”或“词”；通常 1 个中文词语、1 个英文单词、1 个数字或 1 个符号计为 1 个 token。

一般情况下模型中 token 和字数的换算比例大致如下：

1 个英文字符 ≈ 0.3 个 token。
1 个中文字符 ≈ 0.6 个 token。
但因为不同模型的分词不同，所以换算比例也存在差异，每一次实际处理 token 数量以模型返回为准，您可以从返回结果的 usage 中查看。
限速
DeepSeek API 不限制用户并发量，我们会尽力保证您所有请求的服务质量。

但请注意，当我们的服务器承受高流量压力时，您的请求发出后，可能需要等待一段时间才能获取服务器的响应。在这段时间里，您的 HTTP 请求会保持连接，并持续收到如下格式的返回内容：

非流式请求：持续返回空行
流式请求：持续返回 SSE keep-alive 注释（: keep-alive）
这些内容不影响 OpenAI SDK 对响应的 JSON body 的解析。如果您在自己解析 HTTP 响应，请注意处理这些空行或注释。

如果 30 分钟后，请求仍未完成，服务器将关闭连接。
错误码
您在调用 DeepSeek API 时，可能会遇到以下错误。这里列出了相关错误的原因及其解决方法。

错误码	描述
400 - 格式错误	原因：请求体格式错误
解决方法：请根据错误信息提示修改请求体
401 - 认证失败	原因：API key 错误，认证失败
解决方法：请检查您的 API key 是否正确，如没有 API key，请先 创建 API key
402 - 余额不足	原因：账号余额不足
解决方法：请确认账户余额，并前往 充值 页面进行充值
422 - 参数错误	原因：请求体参数错误
解决方法：请根据错误信息提示修改相关参数
429 - 请求速率达到上限	原因：请求速率（TPM 或 RPM）达到上限
解决方法：请合理规划您的请求速率。
500 - 服务器故障	原因：服务器内部故障
解决方法：请等待后重试。若问题一直存在，请联系我们解决
503 - 服务器繁忙	原因：服务器负载过高
解决方法：请稍后重试您的请求
请注意，如果您在输入的 messages 序列中，传入了reasoning_content，API 会返回 400 错误。因此，请删除 API 响应中的 reasoning_content 字段，再发起 API 请求，方法如访问样例所示。

访问样例
下面的代码以 Python 语言为例，展示了如何访问思维链和最终回答，以及如何在多轮对话中进行上下文拼接。

非流式
流式
from openai import OpenAI
client = OpenAI(api_key="<DeepSeek API Key>", base_url="https://api.deepseek.com")

# Round 1
messages = [{"role": "user", "content": "9.11 and 9.8, which is greater?"}]
response = client.chat.completions.create(
    model="deepseek-reasoner",
    messages=messages,
    stream=True
)

reasoning_content = ""
content = ""

for chunk in response:
    if chunk.choices[0].delta.reasoning_content:
        reasoning_content += chunk.choices[0].delta.reasoning_content
    else:
        content += chunk.choices[0].delta.content

# Round 2
messages.append({"role": "assistant", "content": content})
messages.append({'role': 'user', 'content': "How many Rs are there in the word 'strawberry'?"})
response = client.chat.completions.create(
    model="deepseek-reasoner",
    messages=messages,
    stream=True
)
# ...
南将介绍如何使用 DeepSeek /chat/completions API 进行多轮对话。

DeepSeek /chat/completions API 是一个“无状态” API，即服务端不记录用户请求的上下文，用户在每次请求时，需将之前所有对话历史拼接好后，传递给对话 API。

下面的代码以 Python 语言，展示了如何进行上下文拼接，以实现多轮对话。

from openai import OpenAI
client = OpenAI(api_key="<DeepSeek API Key>", base_url="https://api.deepseek.com")

# Round 1
messages = [{"role": "user", "content": "What's the highest mountain in the world?"}]
response = client.chat.completions.create(
    model="deepseek-chat",
    messages=messages
)

messages.append(response.choices[0].message)
print(f"Messages Round 1: {messages}")

# Round 2
messages.append({"role": "user", "content": "What is the second?"})
response = client.chat.completions.create(
    model="deepseek-chat",
    messages=messages
)

messages.append(response.choices[0].message)
print(f"Messages Round 2: {messages}")

在第一轮请求时，传递给 API 的 messages 为：

[
    {"role": "user", "content": "What's the highest mountain in the world?"}
]

在第二轮请求时：

要将第一轮中模型的输出添加到 messages 末尾
将新的提问添加到 messages 末尾
最终传递给 API 的 messages 为：

[
    {"role": "user", "content": "What's the highest mountain in the world?"},
    {"role": "assistant", "content": "The highest mountain in the world is Mount Everest."},
    {"role": "user", "content": "What is the second?"}
]
对话前缀续写沿用 Chat Completion API，用户提供 assistant 开头的消息，来让模型补全其余的消息。
注意事项
使用对话前缀续写时，用户需确保 messages 列表里最后一条消息的 role 为 assistant，并设置最后一条消息的 prefix 参数为 True。
用户需要设置 base_url="https://api.deepseek.com/beta" 来开启 Beta 功能。
样例代
下面给出了对话前缀续写的完整 Python 代码样例。在这个例子中，我们设置 assistant 开头的消息为 "```python\n" 来强制模型输出 python 代码，并设置 stop 参数为 ['```'] 来避免模型的额外解释。
from openai import OpenAI

client = OpenAI(
    api_key="<your api key>",
    base_url="https://api.deepseek.com/beta",
)
messages = [
    {"role": "user", "content": "Please write quick sort code"},
    {"role": "assistant", "content": "```python\n", "prefix": True}
]
response = client.chat.completions.create(
    model="deepseek-chat",
    messages=messages,
    stop=["```"],
)
print(response.choices[0].message.content)
在很多场景下，用户需要让模型严格按照 JSON 格式来输出，以实现输出的结构化，便于后续逻辑进行解析。
DeepSeek 提供了 JSON Output 功能，来确保模型输出合法的 JSON 字符串。
注意事项
设置 response_format 参数为 {'type': 'json_object'}。
用户传入的 system 或 user prompt 中必须含有 json 字样，并给出希望模型输出的 JSON 格式的样例，以指导模型来输出合法 JSON。
需要合理设置 max_tokens 参数，防止 JSON 字符串被中途截断。
在使用 JSON Output 功能时，API 有概率会返回空的 content。我们正在积极优化该问题，您可以尝试修改 prompt 以缓解此类问题。
样例代码
这里展示了使用 JSON Output 功能的完整 Python 代码：
import json
from openai import OpenAI

client = OpenAI(
    api_key="<your api key>",
    base_url="https://api.deepseek.com",
)
system_prompt = """
The user will provide some exam text. Please parse the "question" and "answer" and output them in JSON format.
EXAMPLE INPUT: 
Which is the highest mountain in the world? Mount Everest.
EXAMPLE JSON OUTPUT:
{
    "question": "Which is the highest mountain in the world?",
    "answer": "Mount Everest"
}
"""
user_prompt = "Which is the longest river in the world? The Nile River."
messages = [{"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}]
response = client.chat.completions.create(
    model="deepseek-chat",
    messages=messages,
    response_format={
        'type': 'json_object'
    }
)
print(json.loads(response.choices[0].message.content))
模型将会输出：
{
    "question": "Which is the longest river in the world?",
    "answer": "The Nile River"
}
今天，DeepSeek API 迎来更新，装备了新的接口功能，来释放模型的更多潜力：
更新接口 /chat/completions
JSON Output
Function Calling
对话前缀续写（Beta）
8K 最长输出（Beta）
新增接口 /completions
FIM 补全（Beta）
所有新功能，均可使用 deepseek-chat 和 deepseek-coder 模型调用。
一、更新接口 /chat/completions
1. JSON Output，增强内容格式化
DeepSeek API 新增 JSON Output 功能，兼容 OpenAI API，能够强制模型输出 JSON 格式的字符串。
在进行数据处理等任务时，该功能可以让模型按预定格式返回 JSON，方便后续对模型输出内容进行解析，提高程序流程的自动化能力。
要使用 JSON Output 功能，需要：
设置 response_format 参数为 {'type': 'json_object'}
用户需要在提示词中，指导模型输出 JSON 的格式，来确保输出格式符合预期
合理设置 max_tokens，防止 JSON 字符串被中途截断
以下为一个 JSON Output 功能的使用样例。在这个样例中，用户给出一段文本，模型对文本中的问题&答案进行格式化输出。
详细使用方法，请参考 JSON Output 指南。
2. Function，连接物理世界
DeepSeek API 新增 Function Calling 功能，兼容 OpenAI API，通过调用外部工具，来增强模型与物理世界交互的能力。
Function Calling 功能支持传入多个 Function（最多 128 个），支持并行 Function 调用。
下图展示了将 deepseek-coder 整合到开源大模型前端 LobeChat 的效果。在这个例子中，我们开启了“网站爬虫”插件，来实现对网站的爬取和总结。
下图展示了使用 Function Calling 功能的交互过程：
详细使用方法，请参考 Function Calling 指南。
3. 对话前缀续写（Beta），更灵活的输出控制
对话前缀续写沿用了对话补全的 API 格式，允许用户指定最后一条 assistant 消息的前缀，来让模型按照该前缀进行补全。该功能也可用于输出长度达到 max_tokens 被截断后，将被截断的消息进行拼接，重新发送请求对被截断内容进行续写。
要使用对话前缀续写功能，需要：
设置 base_url 为 https://api.deepseek.com/beta 来开启 Beta 功能
确保 messages 列表里最后一条消息的 role 为 assistant，并设置最后一条消息的 prefix 参数为 True，如：{"role": "assistant": "content": "在很久很久以前，", "prefix": True}
以下为对话前缀续写功能的使用样例。在这个例子里，设置了 assistant 消息开头为'```python\n'，以强制其以代码块开始，并设置 stop 参数为 '```'，让模型不输出多余的内容。
详细使用方法，请参考 对话前缀续写指南。
4. 8K 最长输出（Beta），释放更长可能
为了满足更长文本输出的场景，我们在 Beta 版 API 中，将 max_tokens 参数的上限调整为 8K。
要提高到 8K 最长输出，需要：
设置 base_url 为 https://api.deepseek.com/beta 来开启 Beta 功能
max_tokens 默认为 4096。开启 Beta 功能后，max_tokens 最大可设置为 8192
二、新增接口 /completions
1. FIM 补全（Beta），使能续写场景
DeepSeek API 新增 FIM (Fill-In-the-Middle) 补全接口，兼容 OpenAI 的 FIM 补全 API，允许用户提供自定义的前缀/后缀（可选），让模型进行内容补全。该功能常用于故事续写、代码补全等场景。FIM 补全接口收费与对话补全相同。
要使用 FIM 补全接口，需要设置 base_url 为 https://api.deepseek.com/beta 来开启 Beta 功能。
以下为 FIM 补全接口的使用样例。在这个例子中，用户提供斐波那契数列函数的开头和结尾，模型对中间内容进行补全。
详细使用方法，请参考 FIM 补全指南。
更新说明
Beta 接口已开放给所有用户使用，用户需要设置 base_url 为 https://api.deepseek.com/beta 来开启 Beta 功能。
Beta 接口属于不稳定接口，后续测试、发布计划会灵活变动，敬请谅解。
相关模型版本，在功能稳定后会发布到开源社区，敬请期待。
deepseek-reasoner 是支持推理模式的 DeepSeek 模型。在输出最终回答之前，模型会先输出一段思维链内容，以提升最终答案的准确性。我们的 API 向用户开放 deepseek-reasoner 思维链的内容，以供用户查看、展示、蒸馏使用。
API 参数
输入参数：
max_tokens：模型单次回答的最大长度（含思维链输出），默认为 32K，最大为 64K。
输出字段：
reasoning_content：思维链内容，与 content 同级，访问方法见访问样例。
content：最终回答内容。
支持的功能：Json Output、对话补全，对话前缀续写 (Beta)
不支持的功能：Function Calling、FIM 补全 (Beta)
不支持的参数：temperature、top_p、presence_penalty、frequency_penalty、logprobs、top_logprobs。请注意，为了兼容已有软件，设置 temperature、top_p、presence_penalty、frequency_penalty 参数不会报错，但也不会生效。设置 logprobs、top_logprobs 会报错。
上下文拼
在每一轮对话过程中，模型会输出思维链内容（reasoning_content）和最终回答（content）。在下一轮对话中，之前轮输出的思维链内容不会被拼接到上下文中，如下图所示：
请注意，如果您在输入的 messages 序列中，传入了reasoning_content，API 会返回 400 错误。因此，请删除 API 响应中的 reasoning_content 字段，再发起 API 请求，方法如访问样例所示。
访问样例
下面的代码以 Python 语言为例，展示了如何访问思维链和最终回答，以及如何在多轮对话中进行上下文拼接。
非流式
流式
from openai import OpenAI
client = OpenAI(api_key="<DeepSeek API Key>", base_url="https://api.deepseek.com")

# Round 1
messages = [{"role": "user", "content": "9.11 and 9.8, which is greater?"}]
response = client.chat.completions.create(
    model="deepseek-reasoner",
    messages=messages
)
reasoning_content = response.choices[0].message.reasoning_content
content = response.choices[0].message.content
# Round 2
messages.append({'role': 'assistant', 'content': content})
messages.append({'role': 'user', 'content': "How many Rs are there in the word 'strawberry'?"})
response = client.chat.completions.create(
    model="deepseek-reasoner",
    messages=messages
)
# ...