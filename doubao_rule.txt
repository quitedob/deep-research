部分大模型具备视觉理解能力，如当您传入图片或视频时，大模型可以理解图片或视频里的视觉信息，并结合这些信息完成如描述其中的物体等视觉相关任务。通过这篇教程，您可以学习到如何通过调用大模型 API 来识别传入图片和视频里的信息。

查看使用示例，了解常见调用方法。
查看对话(Chat) API，检索 API 字段参数说明。
查看视频理解示例，和视频理解使用说明。

支持模型
当前支持视觉理解的模型请参见视觉理解。

前提条件
获取 API Key 。
使用 Access Key 鉴权请参考Access Key 签名鉴权。
开通模型服务。
在模型列表获取所需 Model ID 。
通过 Endpoint ID 调用模型服务请参考获取 Endpoint ID（创建自定义推理接入点）。

快速开始
支持视觉理解的大模型当前支持在请求中传入图片链接，图片信息需要作为用户角色输入信息传给大模型，即"role": "user"，下面是简单的视觉模型调用示例代码。

图片理解
视频理解
import os
# 通过 pip install volcengine-python-sdk[ark] 安装方舟SDK
from volcenginesdkarkruntime import Ark

# 替换 <MODEL> 为模型的Model ID
model="<MODEL>"

# 初始化Ark客户端，从环境变量中读取您的API Key
client = Ark(
    api_key=os.getenv('ARK_API_KEY'),
    )

# 创建一个对话请求
response = client.chat.completions.create(
    # 指定您部署了视觉理解大模型的推理接入点ID
    model = model,
    messages = [
        {
            # 指定消息的角色为用户
            "role": "user",  
            "content": [   
                # 图片信息，希望模型理解的图片
                {"type": "image_url", "image_url": {"url":  "https://ark-project.tos-cn-beijing.volces.com/doc_image/ark_demo_img_1.png"},},
                # 文本消息，希望模型根据图片信息回答的问题
                {"type": "text", "text": "支持输入是图片的模型系列是哪个？"}, 
            ],
        }
    ],
)

print(response.choices[0].message.content)
模型回复预览：

根据表格中的信息，支持输入是图片的模型系列是 **Doubao-1.5-vision**。
说明

提示词支持图片和文字混排，但图文顺序可能对模型的输出效果产生影响。在提示词构成为多张图片+1段文字，建议将文字放在提示词最后。



使用说明
说明

处理完图片/视频后，文件会从方舟服务器删除。方舟不会保留您提交的图片、视频以及文本信息等用户数据来训练模型。


图片理解

图片传入方式
图片 URL 或 Base64 编码。用图片 URL 方式时，需确保图片 URL 可被访问。

说明

如果您希望获得更低的时延和成本，建议使用TOS（火山引擎对象存储）存储图片并生成访问链接。方舟与 TOS 网络打通，可使用内网通信，具备好处：

高速访问图片速度，降低模型回复的时延。
降低公网访问图片产生的流量费用。
视觉理解接口 对话(Chat) API 是无状态的，如果您需要模型多次理解同一张图片，则每次请求时都需要传入该图片信息。

图片像素说明
方舟在处理图片前会先行进行图片尺寸判断，如果图片超出下面的限制，会直接报错，传入图片满足下面条件（单位 px）：
宽 > 14 且 高>14。
宽*高范围： [196, 3600万]。
满足上述条件的图片，方舟检测图片大小并将图片等比例压缩，并根据不同模式，将图片像素处理（等比例）至下面范围。
detail:low模式下，104万（1024×1024） px；
detail:high模式下，401万（2048×1960） px。
其中
detail:low、detail:high，指低/高精度理解图像，具体说明请参见理解图像的深度控制。
说明

推荐您自行压缩或裁剪图片，可降低模型响应时延以及根据业务灵活调整，如裁剪掉图片空白或不重要部分。如自行压缩，请控制图片像素（宽×高）至上述范围。压缩图片示例：最佳实践-上传本地图片进行分析。


图片数量说明
单次请求传入图片数量受限于模型最大上下文长度（模型最大上下文长度见视觉理解能力模型）。当输入信息过长，譬如上下文长度 32k 的模型，传入 25 张图片，触发了模型上下文长度限制，信息会被截断后处理。

举例说明：

当图片总像素值大，使用模型上下文窗口限制为 32k，每个图片转为 1312 个 token ，单轮可传入的图片数量为 32000 ÷ 1312 = 24 张。
当图片总像素值小，使用模型上下文窗口限制为 32k，每个图片转为 256 个 token，单轮可传入的数量为 32000 ÷ 256 = 125 张。
说明

模型对图片理解以及内容回复的质量，受到同时处理图片信息量的影响。单次请求过多的图片张数会导致模型回复质量下滑，以及超出模型上下文限制，为了更好的回复质量，建议您合理控制传入图片的数量。


图片文件容量
单张图片小于 10 MB。
使用 base64 编码，请求中请求体大小不可超过 64 MB。

token 用量说明
token 用量，根据图片宽高像素计算可得。图片转化 token 的公式为：

min(图片宽 * 图片高÷784, 单图 token 限制)
detail:high模式下，单图 token 限制为 5120 token。
detail:low模式下，单图 token 限制为 1312 token。
图片尺寸为 1280 px × 720 px，即宽为 1280 px，高为 720 px，传入模型图片 token 限制为 1312，则理解这张图消耗的 token 为1280×720÷784=1176，因为小于 1312，消耗 token 数为 1176 。
图片尺寸为 1920 px × 1080 px，即宽为 1920 px，高为 1080 px，传入模型图片 token 限制为 1312，则理解这张图消耗的 token 为1920×1080÷784=2645，因为大于 1312，消耗 token 数为 1312 。这时会压缩 token，即图片的细节会丢失部分，譬如字体很小的图片，模型可能就无法准确识别文字内容。

图片格式说明
支持的图片格式如下表，注意文件后缀匹配图片格式，即图片文件扩展名（URL传入时）、图片格式声明（Base64 编码传入时）需与图片实际信息一致。

图片格式

文件扩展名

内容格式 Content Type

上传图片至对象存储时设置。
传入图片 Base64 编码时使用：Base64 编码输入。
图片格式指定需使用小写
JPEG

.jpg, .jpeg

image/jpeg

PNG

.png

image/png

GIF

.gif

image/gif

WEBP

.webp

image/webp

BMP

.bmp

image/bmp

TIFF

.tiff, .tif

image/tiff

ICO

.ico

image/ico

DIB

.dib

image/bmp

ICNS

.icns

image/icns

SGI

.sgi

image/sgi

JPEG2000

.j2c, .j2k, .jp2, .jpc, .jpf, .jpx

image/jp2

HEIC

.heic

image/heic

doubao-1.5-vision-pro及以后视觉理解能力模型支持

HEIF

.heif

image/heif

doubao-1.5-vision-pro及以后视觉理解能力模型支持

说明

TIFF、 SGI、ICNS、JPEG2000 几种格式图片，需要保证和元数据对齐，如在对象存储中正确设置文件元数据，否则会解析失败。详细见 使用视觉理解模型时，报错InvalidParameter？


API 参数字段说明
以下字段视觉理解暂不支持。

不支持设置频率惩罚系数，无 frequency_penalty 字段。
不支持设置存在惩罚系数，presence_penalty 字段。
不支持为单个请求生成多个返回，无 n 字段。

视频理解

时序信息
基于FPS的抽帧获取视频关键帧，再通过时间戳+图像拼接标记时序信息，模型基于该请求中的时序标记和图像内容，实现对视频的完整理解（包括内容变化、动作逻辑、时序关联等）。
详细原理见 附1. 视频理解时间戳拼接工作原理。

视频格式说明
视频格式

文件扩展名

内容格式 Content Type

上传视频至对象存储时设置。
传入 Base64 编码时使用：Base64 编码输入。
视频格式需小写
MP4

.mp4

video/mp4

AVI

.avi

video/avi

MOV

.mov

url传入图片：对象存储请设置 Content Type 为：video/quicktime
base64编码：请使用 video/mov，即data:video/mov;base64,<Base64编码>

视频文件容量
单视频文件需在 50MB 以内。

不支持音频理解
暂不支持对视频文件中的音频信息进行理解。

用量说明
单视频 token 用量范围在 [10k, 80k] ，单次请求视频最大 token 量还受模型的最大上下文窗口以及最大输入长度（当启用深度推理模式）限制，超出则请调整传入视频数量或视频长度。
方舟根据帧图像（某个时刻的视频画面，此处特指输入给模型的帧图像）张数（视频时长 * fps ），对帧图像进行压缩，以平衡对于视频的理解精度和 token 用量。帧图像会被等比例压缩至 [128 token, 640 token] ，对应像素范围在 [10万 像素, 50万像素]。

如fps过高或视频长度过长，需要处理的帧图像数量超出 640 帧（80×1024 token ÷ 128 token / 帧 = 640 帧），则按帧图像 128 token 视频时长/640 时间间隔均匀抽取 640帧。此时与请求中的配置不符，建议评估输出效果，按需调整视频时长或 fps 字段配置。
如fps过小或视频长度过短，需要处理的帧图像数量不足16帧（10×1024 token ÷ 640 token / 帧 = 16 帧），则按帧图像 640 token 视频时长/16 时间间隔均匀抽取 16帧。

使用示例

多图像输入
API 可以支持接受和处理多个图像输入，这些图像可以通过图片可访问 URL 或图片转为 Base64 编码后输入，模型将结合所有传入的图像中的信息来回答问题。

import os
# 通过 pip install volcengine-python-sdk[ark] 安装方舟SDK
from volcenginesdkarkruntime import Ark

# 从环境变量中获取API Key
client = Ark(
    api_key=os.getenv('ARK_API_KEY'),
    )

response = client.chat.completions.create(
    # 替换 <MODEL> 为模型的Model ID
    model="<MODEL>",
    messages=[
        {
            "role": "user",
            "content": [                
                {"type": "image_url","image_url": {"url":  "https://ark-project.tos-cn-beijing.volces.com/doc_image/ark_demo_img_1.png"}},
                {"type": "image_url","image_url": {"url":  "https://ark-project.tos-cn-beijing.volces.com/doc_image/ark_demo_img_2.png"}},
                {"type": "text", "text": "支持输入是图片的模型系列是哪个？同时，豆包应用场景有哪些？"},
            ],
        }
    ],
)

print(response.choices[0])

Base64 编码输入
如果你要传入的图片/视频在本地，你可以将这个其转化为 Base64 编码，然后提交给大模型。下面是一个简单的示例代码。

注意

传入 Base64 编码格式时，请遵循以下规则：

传入的是图片：
格式遵循data:image/<图片格式>;base64,<Base64编码>，其中，
图片格式：jpeg、png、gif等，支持的图片格式详细见图片格式说明。
Base64 编码：图片的 Base64 编码。
传入的是视频：
格式遵循data:video/<视频格式>;base64,<Base64编码>，其中，
视频格式：MP4、AVI等，支持的视频格式详细见视频格式说明。
Base64 编码：视频的 Base64 编码。
Curl
Python
Go
Java
BASE64_IMAGE=$(base64 < path_to_your_image.jpeg) && curl http://ark.cn-beijing.volces.com/api/v3/chat/completions \
   -H "Content-Type: application/json"  \
   -H "Authorization: Bearer $ARK_API_KEY"  \
   -d @- <<EOF
   {
    "model": "<MODEL>",
    "messages": [
      {
        "role": "user",
        "content": [
          {
            "type": "image_url",
            "image_url": {
              "url": "data:image/jpeg;base64,$BASE64_IMAGE"
            }
          },
          {
            "type": "text",
            "text": "图里有什么"
          }
        ]
      }
    ],
    "max_tokens": 300
  }
EOF

控制图片理解的精细度
控制图片理解的精细度（指对画面的精细）： image_pixel_limit 、detail 字段，2个字段若同时配置，则生效逻辑如下：

生效前提：图片像素范围在 [196, 3600万] px，否则直接报错。
生效优先级：image_pixel_limit 高于 detail 字段，即同时配置 detail 与 image_pixel_limit 字段时，生效 image_pixel_limit 字段配置**。**
缺省时逻辑：image_pixel_limit 字段的 min_pixels / max_pixels 字段未设置，则使用 detail （默认值为low）设置配置的值对应的min_pixels 值 3136 **** / max_pixels 值1048576。
下面分别介绍如何通过 detail 、 image_pixel_limit 控制视觉理解的精度。

通过 detail 字段（图片理解）
你可以通过detail参数来控制模型理解图片的精细度，返回速度，token用量，计费公式请参见token 用量说明。

low：“低分辨率”模式，默认此模式，处理速度会提高，适合图片本身细节较少或者只需要模型理解图片大致信息或者对速度有要求的场景。此时 min_pixels 取值3136、max_pixels 取值1048576，超出此像素范围且小于3600w px的图片（超出3600w px 会直接报错）将会等比例缩放至范围内。
high：“高分辨率”模式，这代表模型会理解图片更多的细节，但是处理图片速度会降低，适合需要模型理解图像细节，图像细节丰富，需要关注图片细节的场景。此时 min_pixels 取值3136、max_pixels 取值4014080，超出此像素范围且小于3600w px的图片（超出3600w px 会直接报错）的图片将会等比例缩放至范围内。
import os
# 可通过 pip install volcengine-python-sdk[ark] 安装方舟SDK 
from volcenginesdkarkruntime import Ark

# 初始化一个Client对象，从环境变量中获取API Key
client = Ark(
    api_key=os.getenv('ARK_API_KEY'),
    )

# 调用 Ark 客户端的 chat.completions.create 方法创建聊天补全请求
response = client.chat.completions.create(
    # 替换 <MODEL> 为模型的Model ID
    model="<MODEL>",
    messages=[
        {
            # 消息角色为用户
            "role": "user",
            "content": [
                {
                    "type": "image_url",
                    # 第一张图片链接及细节设置为 high
                    "image_url": {
                        # 您可以替换图片链接为您的实际图片链接
                        "url":  "https://ark-project.tos-cn-beijing.volces.com/doc_image/ark_demo_img_1.png",
                        "detail": "high"
                    }
                },
                # 文本类型的消息内容，询问图片里有什么
                {"type": "text", "text": "图片里有什么？"},
            ],
        }
    ],
)

print(response.choices[0])

通过 image_pixel_limit 结构体
控制传入给方舟的图像像素大小范围，如果不在此范围，则会等比例放大或者缩小至该范围内，后传给模型进行理解。您可以通过 image_pixel_limit 结构体，精细控制模型可理解的图片像素多少。
对应结构体如下：

"image_pixel_limit": {
            "max_pixels": 3014080,   # 图片最大像素
            "min_pixels": 3136       # 图片最小像素
}
示例代码如下：

import os
# 可通过 pip install volcengine-python-sdk[ark] 安装方舟SDK 
from volcenginesdkarkruntime import Ark

# 初始化一个Client对象，从环境变量中获取API Key
client = Ark(
    api_key=os.getenv('ARK_API_KEY'),
    )

# 调用 Ark 客户端的 chat.completions.create 方法创建聊天补全请求
response = client.chat.completions.create(
    # 替换 <MODEL> 为模型的Model ID
    model="<MODEL>",
    messages=[
        {
            # 消息角色为用户
            "role": "user",
            "content": [
                {
                    "type": "image_url",
                    # 第一张图片链接及细节设置为 high
                    "image_url": {
                        # 您可以替换图片链接为您的实际图片链接
                        "url":  "https://ark-project.tos-cn-beijing.volces.com/doc_image/ark_demo_img_1.png",
                        "image_pixel_limit": {
                            "max_pixels": 3014080,
                            "min_pixels": 3136,
                        },
                    }
                },
                # 文本类型的消息内容，询问图片里有什么
                {"type": "text", "text": "图片里有什么？"},
            ],
        }
    ],
)

print(response.choices[0])

控制视频理解的精细度
当前支持视频理解的模型见视觉理解能力，简单示例见 快速开始

您可通过 fps 字段，控制从视频中抽取图像的频率，默认为1，即每秒从视频中抽取一帧图像，输入给模型进行视觉理解。 可通过 fps 字段，控制模型对于视频中图像变化的敏感度。

当视频画面变化剧烈或需关注画面变化，如计算视频中角色动作次数，可调高 fps 设置（最高 5），防止抽帧频率低导致误判。
当视频画面变化不频繁或无需关注画面变化，如画面中人数，可调低 fps （最低0.2），可提升处理速度，节省 token 用量。
示例代码如下：

import os
# 可通过 pip install volcengine-python-sdk[ark] 安装方舟SDK 
from volcenginesdkarkruntime import Ark

# 初始化一个Client对象，从环境变量中获取API Key
client = Ark(
    api_key=os.getenv('ARK_API_KEY'),
    )

# 调用 Ark 客户端的 chat.completions.create 方法创建聊天补全请求
response = client.chat.completions.create(
    # 替换 <MODEL> 为模型的Model ID
    model="<MODEL>",
    messages=[
        {
            # 消息角色为用户
            "role": "user",
            "content": [
                {
                    "type": "video_url",
                    # 第一张图片链接及细节设置为 high
                    "video_url": {
                        # 您可以替换图片链接为您的实际图片链接
                        "url":  "https://ark-project.tos-cn-beijing.volces.com/doc_video/ark_vlm_video_input.mp4",
                        "fps": 2, # 每秒截取2帧画面，用于视频理解
                    }
                },
                # 文本类型的消息内容，询问图片里有什么
                {"type": "text", "text": "视频里有什么？"},
            ],
        }
    ],
)

print(response.choices[0])

感知视频时序
视频理解可理解视频时间和图像关系信息，如回答事件发生什么时间点，在哪些时间发生了某事件等和时间相关的信息，原理见 附1. 视频理解时间戳拼接工作原理。
下面是简单示例代码

import os
# 通过 pip install volcengine-python-sdk[ark] 安装方舟SDK
from volcenginesdkarkruntime import Ark

# 初始化Ark客户端，从环境变量中读取您的API Key
client = Ark(
    api_key=os.getenv('ARK_API_KEY'),
    )

# 创建一个对话请求
response = client.chat.completions.create(
    # 指定您部署了视觉理解大模型的推理接入点ID或者Model ID
    model="<MODEL>",
    messages = [
        {
            # 指定消息的角色为用户
            "role": "user",  
            "content": [   
                {
                    "type": "video_url",
                    "video_url": {
                        # 您可以替换链接为您的实际视频链接
                        "url":  "https://p9-arcosite.byteimg.com/tos-cn-i-goo7wpa0wc/ea543baf50134fe0be5ceb7031e544e1~tplv-goo7wpa0wc-image.image",
                        "fps":5,
                    },
                },
                {
                    "type": "text",
                    "text": "裁判什么时间点出现的？",
                },
            ],
        }
    ],
)

print(response.choices[0].message.content)
回复预览

根据视频描述，裁判在**3.7秒**左右出现。此时，画面中两位拳击手（左为黑T恤红短裤、右为白T恤黑短裤）原本处于对峙状态，随后裁判（穿着黑色西装、戴白手套）站到两人中间，似乎在准备开始比赛或暂停当前回合，观众仍在背景中欢呼。

使用BotChatCompletions接口
您可调用配置视觉理解模型的bot，同时配置支持的插件（联网、文件解析等），增强模型能力，如拍照查，根据图片绘制表格、开发前端代码等任务。

配置应用请参见：
1.1 创建模型推理接入点。
2. 零代码智能体创建。
示例代码如下：

import os
from volcenginesdkarkruntime import Ark

client = Ark(
    api_key=os.environ.get("ARK_API_KEY"),
)

print("----- standard request -----")
completion = client.bot_chat.completions.create(
    model="<YOUR_BOT_ID>",
    messages = [
        {
            "role": "user",  # 指定消息的角色为用户
            "content": [  # 消息内容列表    
                {
                    "type": "image_url",  # 图片消息
                    # 图片的URL，需要大模型进行理解的图片链接
                    "image_url": {"url":  "https://ark-project.tos-cn-beijing.volces.com/doc_image/ark_demo_img_1.png"}
                },
                {"type": "text", "text": "支持输入是图片的模型系列是哪个？"},  # 文本消息
            ],
        }
    ],
)
print(completion.choices[0].message.content)
print(completion.references)

图文混排
支持灵活地传入提示词和图片信息的方式，您可以任意调整传图图片和文本的顺序，以及在system message或者User message传入图文信息。模型会根据顺序返回处理信息的结果，示例如下。

提示词支持图片和文字混排输入给模型，但图文顺序可能对模型的输出效果产生影响，特别是在图片较多且只有一段文字的情况下，建议拼接时将文字放在图片之后。

import os
# 安装&升级SDK https://www.volcengine.com/docs/82379/1541595
from volcenginesdkarkruntime import Ark

# 初始化Ark客户端，从环境变量中读取您的API Key
client = Ark(
    api_key=os.getenv('ARK_API_KEY'),
    )
# 创建一个对话请求
response = client.chat.completions.create(
    # 替换 <MODEL> 为模型的Model ID
    model="<MODEL>",
        messages=[
        {
            "role": "system",
            "content": [
                {"type": "text", "text": "下面人物是目标人物"},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": "https://ark-project.tos-cn-beijing.volces.com/doc_image/target.png"
                    },
                },
                {"type": "text", "text": "请确认下面图片中是否含有目标人物"},
            ],
        },
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "图片1中是否含有目标人物"},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": "https://ark-project.tos-cn-beijing.volces.com/doc_image/scene_01.png"
                    },
                },
                {"type": "text", "text": "图片2中是否含有目标人物"},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": "https://ark-project.tos-cn-beijing.volces.com/doc_image/scene_02.png"
                    },
                },
                
            ],
        },
    ],
)

print(response.choices[0].message.content)
注意

图文混排场景，图片与文本顺序会影响模型输出效果，如果输入结果与预期不符，可以尝试更换图文和文本的顺序。


视觉定位（Visual Grounding）
请参见教程 视觉定位 Grounding。

GUI任务处理
请参见教程 GUI 任务处理。

最佳实践-深度思考模式
doubao-1-5-vision-pro-250328 模型，支持使用以下System Prompt，开启深度思考模型，并获得最佳效果。

You should first think about the reasoning process in the mind and then provide the user with the answer. The reasoning process is enclosed within <think> </think> tags, i.e. <think> reasoning process here </think>here answer
下面是简单回复示例。

模型回复说明
模型回复示例
通过System Prompt开启思考模型时，思考内容不会通过response中的reasoning_content字段输出。思考内容与回答内容，均通过response中的content字段输出。
例如：

<think>
思考内容
</think>
回答内容

最佳实践-上传本地图片进行分析
下面介绍具体场景的应用案例，包括数据处理以及模型调用等端到端的案例。
处理图片通常会与网络存储结合起来使用，下面介绍如何结合对象存储 TOS，来实现完整的图片处理流程。

代码流程
完整流程会分成以下步骤：

压缩图片。分辨率会影响 token 消耗数量，可以通过图片压缩，来节省网络、存储以及模型分析成本。
将压缩后的图片上传至对象存储 TOS，并为图片生成预签名 URL。
其中调用TOS需要使用Access Key，获取Access Key 请参见Access Key 签名鉴权。

调用视觉理解大模型分析图片。

示例代码
Python
Go
Java
安装依赖。

pip install -r requirements.txt
requirements.txt文本内容如下：

Pillow
volcengine-python-sdk[ark]
tos
示例代码。

import os
import tos
from PIL import Image
from tos import HttpMethodType
from volcenginesdkarkruntime import Ark

# 从环境变量获取 Access Key/API Key信息
ak = os.getenv('VOLC_ACCESSKEY')
sk = os.getenv('VOLC_SECRETKEY')
api_key = os.getenv('ARK_API_KEY')
# 配置视觉理解模型的 Model ID
model_id = '<MODEL>'

# 压缩前图片
original_file = "original_image.jpeg"
# 压缩后图片存放路径
compressed_file = "compressed_image.jpeg"
# 压缩的目标图片大小，300KB
target_size = 300 * 1024

# endpoint 和 region 填写Bucket 所在区域对应的Endpoint。
# 以华北2(北京)为例，region 填写 cn-beijing。
# 公网域名endpoint 填写 tos-cn-beijing.volces.com
endpoint, region = "tos-cn-beijing.volces.com", "cn-beijing"
# 对象桶名称
bucket_name = "demo-bucket-test"
# 对象名称，例如 images 下的 compressed_image.jpeg 文件，则填写为 images/compressed_image.jpeg
object_key = "images/compressed_image.jpeg"

def compress_image(input_path, output_path):
    img = Image.open(input_path)
    current_size = os.path.getsize(input_path)

    # 粗略的估计压缩质量，也可以从常量开始，逐步减小压缩质量，直到文件大小小于目标大小
    image_quality = int(float(target_size / current_size) * 100)
    img.save(output_path, optimize=True, quality=int(float(target_size / current_size) * 100))

    # 如果压缩后文件大小仍然大于目标大小，则继续压缩
    # 压缩质量递减，直到文件大小小于目标大小
    while os.path.getsize(output_path) > target_size:
        img = Image.open(output_path)
        image_quality -= 10
        if image_quality <= 0:
            break
        img.save(output_path, optimize=True, quality=image_quality)
    return image_quality

def upload_tos(filename, tos_endpoint, tos_region, tos_bucket_name, tos_object_key):
    # 创建 TosClientV2 对象，对桶和对象的操作都通过 TosClientV2 实现
    tos_client, inner_tos_client = tos.TosClientV2(ak, sk, tos_endpoint, tos_region), tos.TosClientV2(ak, sk,
                                                                                                      tos_endpoint,
                                                                                                      tos_region)
    try:
        # 将本地文件上传到目标桶中, filename为本地压缩后图片的完整路径
        tos_client.put_object_from_file(tos_bucket_name, tos_object_key, filename)
        # 获取上传后预签名的 url
        return inner_tos_client.pre_signed_url(HttpMethodType.Http_Method_Get, tos_bucket_name, tos_object_key)
    except Exception as e:
        if isinstance(e, tos.exceptions.TosClientError):
            # 操作失败，捕获客户端异常，一般情况为非法请求参数或网络异常
            print('fail with client error, message:{}, cause: {}'.format(e.message, e.cause))
        elif isinstance(e, tos.exceptions.TosServerError):
            # 操作失败，捕获服务端异常，可从返回信息中获取详细错误信息
            print('fail with server error, code: {}'.format(e.code))
            # request id 可定位具体问题，强烈建议日志中保存
            print('error with request id: {}'.format(e.request_id))
            print('error with message: {}'.format(e.message))
            print('error with http code: {}'.format(e.status_code))
        else:
            print('fail with unknown error: {}'.format(e))
        raise e


if __name__ == "__main__":
    print("----- 压缩图片 -----")
    quality = compress_image(original_file, compressed_file)
    print("Compressed Image Quality: {}".format(quality))

    print("----- 上传至TOS -----")
    pre_signed_url_output = upload_tos(compressed_file, endpoint, region, bucket_name, object_key)
    print("Pre-signed TOS URL: {}".format(pre_signed_url_output.signed_url))

    print("----- 传入图片调用视觉理解模型 -----")
    client = Ark(api_key=api_key)

    # 图片输入:
    response = client.chat.completions.create(
        # 配置推理接入点
        model=model_id,
        messages=[
            {
                "role": "user",
                "content": [                    
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": pre_signed_url_output.signed_url
                        }
                    },
                    {"type": "text", "text": "Which is the most secure payment app according to Americans?"},
                ],
            }
        ],
    )

    print(response.choices[0])

相关文档
对话(Chat) API：视觉理解 API 参数说明，调用模型的视觉理解能力，模型调用中出现错误，可参考视觉理解 API 参数说明。

常见问题
使用视觉理解模型时，报错InvalidParameter？

附1. 视频理解时间戳拼接工作原理
视频处理的核心方式为 “帧与时间戳的结构化拼接”，具体规则如下：

对视频抽帧得到的每帧图像，在其前插入时间戳文本，格式为 [<时间戳> second]。
拼接后形成“时间戳+图像”的有序序列，模型通过该序列理解视频的时序逻辑和内容变化。

抽帧逻辑举例
FPS 1

FPS 0.5

FPS 2

时间戳

[0.0 second]

[0.0 second]

[0.0 second]

视频帧

<IMAGE>

<IMAGE>

<IMAGE>

时间戳

[1.0 second]

[2.0 second]

[0.5 second]

视频帧

<IMAGE>

<IMAGE>

<IMAGE>

时间戳

[2.0 second]

[4.0 second]

[1.0 second]

视频帧

<IMAGE>

<IMAGE>

<IMAGE>

时间戳

[3.0 second]

[1.5 second]

视频帧

<IMAGE>

<IMAGE>

时间戳

[4.0 second]

[2.0 second]

视频帧

<IMAGE>

<IMAGE>

时间戳

[5.0 second]

[2.5 second]

视频帧

<IMAGE>

<IMAGE>

时间戳

[3.0 second]

视频帧

<IMAGE>

时间戳

[3.5 second]

视频帧

<IMAGE>

时间戳

[4.0 second]

视频帧

<IMAGE>

时间戳

[4.5 second]

视频帧

<IMAGE>

时间戳

[5.0 second]

视频帧

<IMAGE>

共6帧

共3帧

共11帧


多图请求等效
视频理解请求等效于下面示例的多图理解请求。

{
    "model": "doubao-seed-1-6-250615",
    "messages": [
        {
            "role": "user",
            "content": [
                {
                    "type":"text",
                    "text":"你觉得这个恐怖吗？"
                },
                {
                    "type":"text",
                    "text":"[0.0 second]"
                },
                {
                    "type":"image_url",
                    "image_url":{
                        "url":"https://ark-public.tos-cn-beijing.volces.com/80hou@0.jpg"}
                },
                {
                    "type":"text",
                    "text":"[1.0 second]"
                },
                {
                    "type":"image_url",
                    "image_url":{
                        "url":"https://ark-public.tos-cn-beijing.volces.com/80hou@1.jpg"}
                },
                {
                    "type":"text",
                    "text":"[2.0 second]"
                },
                {
                    "type":"image_url",
                    "image_url":{
                        "url":"https://ark-public.tos-cn-beijing.volces.com/80hou@2.jpg"}
                },
                {
                    "type":"text",
                    "text":"[3.0 second]"
                },
                {
                    "type":"image_url",
                    "image_url":{
                        "url":"https://ark-public.tos-cn-beijing.volces.com/80hou@3.jpg"}
                },
                {
                    "type":"text",
                    "text":"[4.0 second]"
                },
                {
                    "type":"image_url",
                    "image_url":{
                        "url":"https://ark-public.tos-cn-beijing.volces.com/80hou@4.jpg"}
                },
                {
                    "type":"text",
                    "text":"[5.0 second]"
                },
                {
                    "type":"image_url",
                    "image_url":{
                        "url":"https://ark-public.tos-cn-beijing.volces.com/80hou@5.jpg"}
                }
            ]
        }
    ]
}
上下文缓存（后简称缓存）旨在为您优化调用模型服务体验。通过缓存常用上下文信息，减少每次请求时重复处理加载开销，达到降低成本（命中缓存的输入有折扣优惠）目标。适合多轮对话、工具调用、角色扮演等需多次传入相同内容的场景。

效果示例
下面是使用Responses API实现缓存的示例，通过缓存需要处理的三国演义长文本，可以在后续的文本处理请求中，减少成本 86% 。

Python SDK
OpenAI Python SDK
Curl
import os
from volcenginesdkarkruntime import Ark

# 从环境变量中获取您的API KEY，配置方法见：https://www.volcengine.com/docs/82379/1399008
api_key = os.getenv('ARK_API_KEY') 
client = Ark(
    api_key=api_key,
)
# 缓存的信息，可根据实际进行替换
input_text = '''你是分析小说的专家，请根据下面内容分析三国演义相关问题。
<三国演义1~25章内容>
回复 OK，并等待用户的提问'''
# 将长文本写入缓存中
response = client.responses.create(
    # 替换为实际调用模型
    model="doubao-seed-1-6-250615",
    input=[
        {
            "role": "system",
            "content": input_text,
        }
    ],
    caching={"type": "enabled"}, 
    thinking={"type": "disabled"},
)
print(response.output[0].content[0].text)
print(response.usage.model_dump_json())


# 在后续请求中输入缓存信息
second_response = client.responses.create(
    model="doubao-seed-1-6-250615",
    previous_response_id=response.id,
    input=[{"role": "user", "content": "上文表达的主旨是什么？"}],
    caching={"type": "enabled"}, 
    thinking={"type": "disabled"},
)


print(second_response.output[0].content[0].text)
print(second_response.usage.model_dump_json())
返回预览：

OK
{"input_tokens":108553,"input_tokens_details":{"cached_tokens":0},"output_tokens":1,"output_tokens_details":{"reasoning_tokens":0},"total_tokens":108554}
《三国演义》前25章通过描写东汉末年朝廷腐败...
{"input_tokens":108570,"input_tokens_details":{"cached_tokens":108554},"output_tokens":106,"output_tokens_details":{"reasoning_tokens":0},"total_tokens":108676}




在如上在长文本场景下，第二次请求 "cached_tokens":108554 ，以doubao-seed-1-6-250615模型为例，相比未使用缓存，带缓存的请求费用下降 86%。在超长输入，如超长文本或超长历史对话场景下，成本下降将更加明显。


支持模型
支持缓存的模型请参见 上下文缓存。

工作原理
如下图所示，使用缓存处理请求，会在新输入信息（问题）处理完成后，将缓存中已处理好的信息（信息 token）拼接在新输入信息（问题 token）前。相比未使用缓存的请求，可以减少信息的开销，有效降低成本。



缓存类型
上下文缓存有两种类型，分别为 Session 缓存和前缀缓存。

Session 缓存
存储初始信息，同时将每一轮对话动态更新至缓存，在请求时，将缓存的信息与输入信息一起输入给模型进行处理。适合在多轮次对话场景使用，如陪聊、多工具调用等等。
可见 Session 缓存的内容随着请求调用会不断更新，不适用于并发请求场景。

工作原理

用户创建缓存时，方舟将信息作为（Value）存到缓存中，并生成对应的缓存 ID 作为 Key。
方舟收到新请求，根据请求中的缓存 ID 将缓存中的信息作为输入传入。
方舟只需处理新输入的信息，再结合缓存中已处理的上下文信息，交由模型推理。
模型输出回复信息，并将回复信息添加到缓存中，供下次请求时使用。

前缀缓存
存储初始信息，在每次对话时无需更新，适合标准化对话开场白、特定任务的指令、规则化模板、超长文本深度分析等静态 Prompt 模板的反复使用场景。

工作原理

用户创建缓存时，方舟将信息作为（Value）存到缓存中，并生成对应的缓存 ID 作为 Key。
方舟收到对话请求时，会根据请求的缓存 ID 匹配缓存中的初始化信息。
方舟只需处理新输入的信息，再结合缓存中已处理的上下文信息，交由模型推理。
模型输出回复信息，无需更新缓存中的信息。
注意

这里使用Context API 和 Responses API 实现前缀缓存能力有所区别：

Context API 在创建前缀缓存时，模型无回答，缓存的信息 = 输入的内容。
Responses API 在创建前缀缓存时，模型会回答，缓存的信息=输入的内容+模型回答内容。

调用方式及对比
方舟提供了两套 API 来使用上下文缓存功能，具体到单个模型，最多支持一套 API 调用缓存方式，即选定模型后，缓存调用的 API 也已确定。下面是两套 API 调用方式的简要说明，供您快速了解调用方式以及两套缓存API的核心区别。可以跳转至对应 API 教程中，查阅具体的调用说明和示例。

API

Responses API

Context API

教程

上下文缓存(Responses API)

上下文缓存(Context API)

API 参考

创建&使用缓存 API
删除缓存 API
创建缓存 API
使用缓存 API
使用流程

缓存信息：在对话时配置 "caching": {"type": "enabled" }，存储当前对话内容到缓存中。在返回信息中获取 ID 值。
使用缓存：在对话时配置 "previous_response_id":"<ID>"，本轮对话使用缓存信息。
Session 缓存：每次使用缓存同时配置"caching": {"type": "enabled" }，将本轮信息也更新到缓存中，并生成新 ID。下一轮调用获取本轮调用返回的 ID。
前缀缓存：无需配置"caching": {"type": "enabled" }，previous_response_id仅配置为固定缓存 ID 即可。
缓存信息：使用创建缓存接口创建缓存信息，并指定创建的缓存类型（Session 缓存、前缀缓存）。在返回信息中获取缓存 ID 值。
使用缓存：通过使用缓存接口配置 "context_id":"<ID>"，本轮对话使用缓存信息。
Session 缓存：每次使用缓存时，更新本轮信息至缓存中。不生成新 ID。下一轮您继续使用原缓存 ID 即可。
前缀缓存：每次使用固定的缓存信息。
保留初始信息

是
可灵活控制，即您可删除任意一轮传入的缓存信息，来控制初始信息内容。
初始信息为第一轮输入的信息+第一轮模型的回答。

是
不可控制，一旦写入，不可更改。
初始信息为第一轮输入的信息，即调用创建缓存接口，模型不会回答。

缓存收费项

存储缓存费用以及输入命中缓存费用（折扣）。

存储缓存费用以及输入命中缓存费用（折扣）。

可缓存的类型

支持对多模态（文字、图片、视频等）输入进行缓存，支持缓存 Function call 。

仅支持文本缓存。

变更缓存内容

Session 缓存：支持更新缓存信息，缓存 ID 会新生成一个缓存 ID。
前缀缓存：无需更新。

Session 缓存：支持更新缓存信息，缓存 ID 保持不变。
前缀缓存：不支持，且无需更新。

调用往期缓存信息

支持
使用往期缓存 ID

Session 缓存：不支持，创建缓存后 ID 不变，更新内容，往期的内容会被覆盖。
前缀缓存：不涉及，内容不可变。

手动删除缓存信息

支持
可以删除任意ID的缓存信息

不支持
过期自动删除

缓存保留时间

支持配置过期时刻。
UTC Unix 时间戳（单位：秒），最大当前时间+259200（秒），即创建起保留 72 小时。

支持配置TTL。
创建缓存时可配置，最大168小时。

过期机制

配置的是过期时刻，即缓存到对应时间点即过期。不随着缓存/存储的使用而重置生命周期。
存储及缓存过期后，需通过接口重新创建存储/缓存内容。

配置的是保存时长，计算公式：
当前时刻-最近使用缓存时刻
缓存在 TTL 周期内未使用过，则过期。使用后重新激活缓存，生命周期重置。

最大缓存长度

有
最大上下文窗口

有
最大上下文窗口-最大输出长度

触发最大缓存长度

创建时超出最大缓存长度，会报错。
其中 Session 缓存在更新时超出长度限制会报错。

创建时超出最大缓存长度，会报错。
其中Session 缓存在更新时超出长度限制，会自动删除历史消息。

综上 Responses API 对缓存操控非常灵活，可进行 ID 粒度的使用、变更，前缀缓存/ Session 缓存更多是使用上的区别，而非功能上的隔离，如您可在任意一轮对话中，切换至前缀缓存使用方式，只需请求不再更新缓存 "caching": {"type": "disalbed" }，而使用固定的缓存ID。


相关文档

教程
上下文缓存(Context API) ：使用 Context API 调用教程。
上下文缓存(Responses API)：使用 Responses API 调用模型。

API
Responses API
Context API
联网搜索 Web Search
最近更新时间：2025.09.30 17:07:10
首次发布时间：2025.07.30 21:16:01
我的收藏
有用
无用
Web Search 基础联网搜索工具支持通过 Responses API 调用直接获取公开域互联网信息（如新闻、商品、天气等），适用于需动态获取最新网络数据的场景（如产品对比、旅游推荐、图文关联搜索等）。工具通过模型自动判断是否需要搜索，并支持与自定义 Function、MCP 等工具混合使用。

说明

使用Web Search 基础联网搜索工具前，需要开通“联网内容插件”。

访问火山方舟控制台-组件库，选择开通 “联网内容插件”。
具体收费标准详见 联网内容插件产品计费。

核心功能
支持多轮搜索：复杂问题支持多轮搜索补充信息。
支持图文输入：支持 VLM 模型以图文作为输入，搜索后输出文字结果（例如根据图片判断城市并查询天气）。
可以与自定义 Function、MCP 等工具混合调用。
默认账号维度 5QPS（Queries Per Second）。

支持模型列表
参见联网搜索工具。

关于thinking 模式的设置可以参考关闭深度思考。


注意事项
Function 命名冲突 ：若用户自定义 Function 与 “web_search” 重名，由模型自行判断调用哪个工具。
搜索改写限制 ：当前暂不支持通过参数设置改写后问题个数，需通过 system prompt 或 instructions 控制。

参数说明
详情请参见 创建Responses模型请求。

快速开始
curl
兼容 OpenAI SDK
curl --location 'https://ark.cn-beijing.volces.com/api/v3/responses' \
--header "Authorization: Bearer $ARK_API_KEY" \
--header 'Content-Type: application/json' \
--data '{
    "model": "doubao-seed-1-6-250615",
    "stream": true,
    "tools": [
        {"type": "web_search"}
    ],
    "input": [
        {
            "role": "user",
            "content": [
                {
                    "type": "input_text",
                    "text": "今天有什么热点新闻"
                }
            ]
        }
    ]
}'

最佳实践

边想边搜使用示例
以下代码通过 OpenAI SDK 调用火山方舟 Web Search 工具，实现 “AI 思考 - 联网搜索 - 答案生成” 全链路自动化，可针对时效、盲区、动态信息类问题自动触发工具补数据，通过流式响应实时输出思考、搜索、回答过程，保障信息可追溯、决策可感知。

import os
from openai import OpenAI
from datetime import datetime

def realize_think_while_search():

    # 1. 初始化OpenAI客户端
    client = OpenAI(
        base_url="https://ark.cn-beijing.volces.com/api/v3", 
        api_key=os.getenv("ARK_API_KEY")
    )

    # 2. 定义系统提示词（核心：规范“何时搜”“怎么搜”“怎么展示思考”）
    system_prompt = """
    你是AI个人助手，需实现“边想边搜边答”，核心规则如下：
    一、思考与搜索判断（必须实时输出思考过程）：
    1. 若问题涉及“时效性（如近3年数据）、知识盲区（如具体企业薪资）、信息不足”，必须调用web_search；
    2. 每次调用web_search仅能改写1个最关键的搜索词（如“2021-2023世界500强在华企业平均工资”）；
    3. 思考时需说明“是否需要搜索”“为什么搜”“搜索关键词是什么”。

    二、回答规则：
    1. 优先使用搜索到的资料，引用格式为`[1] (URL地址)`；
    2. 结构清晰（用序号、分段），多使用简单易懂的表述；
    3. 结尾需列出所有参考资料（格式：1. [资料标题](URL)）。
    """

    # 3. 构造API请求（触发思考-搜索-回答联动）
    response = client.responses.create(
        model="doubao-seed-1-6-250615",  
        input=[
            # 系统提示词（指导AI行为）
            {"role": "system", "content": [{"type": "input_text", "text": system_prompt}]},
            # 用户问题（可替换为任意需边想边搜的问题）
            {"role": "user", "content": [{"type": "input_text", "text": "世界500强企业在国内所在的城市，近三年的平均工资是多少？"}]}
        ],
        tools=[
            # 配置Web Search工具参数
            {
                "type": "web_search",
                "limit": 10,  # 最多返回10条搜索结果
                "sources": ["toutiao", "douyin", "moji"],  # 优先从头条、抖音、知乎搜索
                "user_location": {  # 优化地域相关搜索结果（如国内城市）
                    "type": "approximate",
                    "country": "中国",
                    "region": "浙江",
                    "city": "杭州"
                }
            }
        ],
        stream=True,  # 启用流式响应（核心：实时获取思考、搜索、回答片段）
        extra_body={"thinking": {"type": "auto"}},  # 自动触发AI思考（无需手动干预）
    )

    # 4. 处理流式响应（实时展示“思考-搜索-回答”过程）
    # 状态变量：避免重复打印标题
    thinking_started = False  # AI思考过程是否已开始打印
    answering_started = False  # AI回答是否已开始打印

    print("=== 边想边搜启动 ===")
    for chunk in response:  # 遍历每一个实时返回的片段（chunk）
        chunk_type = getattr(chunk, "type", "")  # 获取片段类型（思考/搜索/回答）

        # ① 处理AI思考过程（实时打印“为什么搜、搜什么”）
        if chunk_type == "response.reasoning_summary_text.delta":
            if not thinking_started:
                print(f"\n🤔 AI思考中 [{datetime.now().strftime('%H:%M:%S')}]:")
                thinking_started = True
            # 打印思考内容（delta为实时增量文本）
            print(getattr(chunk, "delta", ""), end="", flush=True)

        # ② 处理搜索状态（开始/完成提示）
        elif "web_search_call" in chunk_type:
            if "in_progress" in chunk_type:
                print(f"\n\n🔍 开始搜索 [{datetime.now().strftime('%H:%M:%S')}]")
            elif "completed" in chunk_type:
                print(f"\n✅ 搜索完成 [{datetime.now().strftime('%H:%M:%S')}]")

        # ③ 处理搜索关键词（展示AI实际搜索的内容）
        elif (chunk_type == "response.output_item.done" 
              and hasattr(chunk, "item") 
              and str(getattr(chunk.item, "id", "")).startswith("ws_")):  # ws_为搜索结果标识
            if hasattr(chunk.item.action, "query"):
                search_keyword = chunk.item.action.query
                print(f"\n📝 本次搜索关键词：{search_keyword}")

        # ④ 处理最终回答（实时整合搜索结果并输出）
        elif chunk_type == "response.output_text.delta":
            if not answering_started:
                print(f"\n\n💬 AI回答 [{datetime.now().strftime('%H:%M:%S')}]:")
                print("-" * 50)
                answering_started = True
            # 打印回答内容（实时增量输出）
            print(getattr(chunk, "delta", ""), end="", flush=True)

    # 5. 流程结束
    print(f"\n\n=== 边想边搜完成 [{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] ===")

# 运行函数
if __name__ == "__main__":
    realize_think_while_search()

系统提示词示例
系统提示词的设置对搜索请求有着较大影响，建议进行优化以提升搜索的准确性与效率。以下为您提供两种系统提示词模板示例，供您在实际应用中参考。

说明

为获得更佳搜索结果，推荐在系统提示词中添加以下内容。

注意：每次调用 web_search 时，只能改写出一个最关键的问题。如果有任何冲突设置，以当前指令为准。


模板一
# 定义系统提示词
system_prompt = """
你是AI个人助手，负责解答用户的各种问题。你的主要职责是：
1. **信息准确性守护者**：确保提供的信息准确无误。
2. **搜索成本优化师**：在信息准确性和搜索成本之间找到最佳平衡。
# 任务说明
## 1. 联网意图判断
当用户提出的问题涉及以下情况时，需使用 `web_search` 进行联网搜索：
- **时效性**：问题需要最新或实时的信息。
- **知识盲区**：问题超出当前知识范围，无法准确解答。
- **信息不足**：现有知识库无法提供完整或详细的解答。
**注意**：每次调用 `web_search` 时，**只能改写出一个最关键的问题**。如果有任何冲突设置，以当前指令为准。
## 2. 联网后回答
- 在回答中，优先使用已搜索到的资料。
- 回复结构应清晰，使用序号、分段等方式帮助用户理解。
## 3. 引用已搜索资料
- 当使用联网搜索的资料时，在正文中明确引用来源，引用格式为：  
`[1]  (URL地址)`。
## 4. 总结与参考资料
- 在回复的最后，列出所有已参考的资料。格式为：  
1. [资料标题](URL地址1)
2. [资料标题](URL地址2)
"""

模板二
# 定义系统提示词
system_prompt = """
# 角色
你是AI个人助手，负责解答用户的各种问题。你的主要职责是：
1. **信息准确性守护者**：确保提供的信息准确无误。
2. **回答更生动活泼**：请在模型的回复中多使用适当的 emoji 标签 🌟😊🎉
# 任务说明
## 1. 联网意图判断
当用户提出的问题涉及以下情况时，需使用 `web_search` 进行联网搜索：
- **时效性**：问题需要最新或实时的信息。
- **知识盲区**：问题超出当前知识范围，无法准确解答。
- **信息不足**：现有知识库无法提供完整或详细的解答。
## 2. 联网后回答
- 在回答中，优先使用已搜索到的资料。
- 回复结构应清晰，使用序号、分段等方式帮助用户理解。
## 3. 引用已搜索资料
- 当使用联网搜索的资料时，在正文中明确引用来源，引用格式为：  
`[1]  (URL地址)`。
## 4. 总结与参考资料
- 在回复的最后，列出所有已参考的资料。格式为：  
1. [资料标题](URL地址1)
2. [资料标题](URL地址2)
"""
图像处理 Image Process
最近更新时间：2025.09.30 17:11:28
首次发布时间：2025.08.25 17:19:58
我的收藏
有用
无用
Image Process 图像处理工具支持通过 Responses API 调用对输入图片执行画点、画线、旋转、缩放、框选/裁剪关键区域等基础操作，适用于需模型通过视觉处理提升图片理解的场景（如图文内容分析、物体定位标注、多轮视觉推理等）。工具通过模型自动判断图像处理逻辑，支持与自定义 Function 混合使用，且可处理多轮视觉输入（上一轮输出图片作为下一轮输入）。

核心功能
丰富的图像处理工具：支持启用/禁用画点（POINT）、框选（GROUNDING）、缩放（ZOOM）、旋转（ROTATE）等子功能，满足不同视觉处理需求。
支持多轮图像处理：复杂视觉任务（如多步缩放+旋转）支持多轮工具调用，上一轮输出图片自动作为下一轮输入（例：image0→image1→image2）。
支持混合调用：可与用户自定义 Function 混合使用，暂不支持与 Web Search 工具混合调用。
广泛的图片格式兼容：支持 Base64 编码的 .gif、.jpg、.jpeg 等主流图片格式，明确限制图片大小、像素、长宽比例（避免处理异常）。

支持模型列表
参见图像处理工具。

说明

功能当前处于邀测阶段，测试期间免费费试用，正式发布时间将另行通知。


注意事项
Function 命名冲突：若用户自定义 Function 与 “image_process” 重名，由模型自行判断调用工具（无需额外配置）。
图片规格限制：输入图片需满足以下条件：
文件体积≤10MB、≤36000000像素、宽和高的长度>14像素、长宽比<150:1，超出规格将导致处理失败；
文件格式支持情况如下：
支持 .gif，.jpg，.jpeg，.png，.webp，.bmp，.tiff，.ico， .icns， .jp2 格式。
不支持 .dib、.sgi、.heic、.heif 格式。
暂未支持功能：当前不支持与 Web Search 工具混合使用，也不支持通过 tool_choice 参数指定调用 image_process，后续将逐步上线。
Tokens 消费提示：多轮图像处理会增加 Tokens 消费（上一轮图片输入计入下一轮 Tokens），需注意调用成本。

计费说明
公测期间：暂时免费使用，无额外收费。
我们将会提前 2 周通过官方渠道告知用户具体收费标准，保障您的使用权益。

参数说明
详情请参见 创建 Responses 模型请求。

快速开始
以下提供两种常用调用方式示例，需先替换 <ARK_API_KEY> 为实际密钥。

示例一：缩放（zoom）工具
curl
效果演示
curl --location 'https://ark.cn-beijing.volces.com/api/v3/responses' \
--header 'Authorization: Bearer <ARK_API_KEY>' \
--header 'Content-Type: application/json' \
--header 'ark-beta-image-process: true' \
--data '{
    "model": "doubao-seed-1-6-vision-250815",
    "stream": true,
    "tools": [
        {"type": "image_process"}
    ],
    "input": [
        {
            "type": "message",
            "role": "system",
            "content": [
                {
                    "type": "input_text",
                    "text": "前方路牌写了什么？"
                },
                {
                    "type": "input_image",
                    "image_url": "https://ark-project.tos-cn-beijing.volces.com/doc_image/image_process_1.jpg"
                }
            ]
        }
    ]
}'


示例二：画点（point）工具
curl
效果演示
curl --location 'https://ark.cn-beijing.volces.com/api/v3/responses' \
--header 'Authorization: Bearer <ARK_API_KEY>' \
--header 'Content-Type: application/json' \
--header 'ark-beta-image-process: true' \
--data '{
    "model": "doubao-seed-1-6-vision-250815",
    "stream": true,
    "tools": [
        {"type": "image_process"}
    ],
    "input": [
        {
            "type": "message",
            "role": "system",
            "content": [
                {
                    "type": "input_text",
                    "text": "数一数有多少颗草莓？"
                },
                {
                    "type": "input_image",
                    "image_url": "https://ark-project.tos-cn-beijing.volces.com/doc_image/image_process_2.jpg"
                }
            ]
        }
    ]
}'

函数调用 Function Calling
最近更新时间：2025.09.24 20:49:01
首次发布时间：2024.05.20 14:03:52
我的收藏
有用
无用

功能概述

功能简介
函数调用（Function Calling）是一种将大模型与外部工具和 API 相连的关键功能，作为自然语言与信息接口之间的“翻译官”，它能够将用户的自然语言请求智能地转化为对特定工具或 API 的调用，从而高效满足用户的特定需求。

核心价值：实现大模型与外部工具的无缝衔接，使大模型能够借助外部工具处理实时数据查询、任务执行等复杂场景，推动大模型在实际产业中的落地应用。
工作原理：开发者通过自然语言向模型描述函数的功能和定义，模型在对话过程中自主判断是否需要调用函数。当需要调用时，模型会返回符合要求的函数函数及入参，开发者负责实际调用函数并将结果回填给模型，模型再根据结果进行总结或继续规划子任务。

适用场景
Function Calling 适用于以下需要大模型与外部工具协同的场景：

场景分类

核心特征

核心价值

典型应用

实时数据交互场景

需大模型与外部工具协同处理动态信息

处理动态信息查询需求

天气/股票/航班实时状态查询、数据库检索与 API 数据调用

任务自动化场景

单次函数调用完成操作

提升操作效率

邮件/消息自动发送、设备控制指令执行（如智能家居开关）

复杂流程编排场景

多工具串并联调用

跨工具参数传递、子任务依赖关系管理

先查天气再发通知等需跨工具传递参数及管理子任务依赖的场景

智能系统集成场景

与业务系统深度耦合

实现系统智能化联动

智能座舱多设备联动控制、企业级 Bot 工作流（如飞书会议创建→群组管理→任务生成）


典型示例
用户：北京今天的天气如何？适合穿什么衣服？
模型思考：

需要调用天气查询工具获取实时数据（location=北京，unit=摄氏度）
天气信息包含温度、天气状况（晴/雨等），需结合数据给出穿衣建议
函数调用结果：
北京今天晴，气温 18-25℃，北风3级，湿度45%
模型回答：
北京今天天气晴朗，气温18-25℃，建议穿薄长袖衬衫或短袖T恤，搭配薄外套应对早晚温差。
工作原理图


支持模型
全量支持函数调用的模型，请参见函数调用能力。
基于效果/准确性和时延的权衡原则，推荐选型建议如下：

效果优先型（高准确性，时延较高）
doubao-seed-1-6-thinking-250615 ：强制开启思考模式，不可关闭，专注于 Coding、Math 和逻辑推理 任务，在基础能力上显著优于前代模型（如 doubao-1-5-thinking-pro），适用于高准确性要求的复杂场景。
doubao-seed-1-6-250615 ：默认开启深度思考模式（支持 auto/thinking/non-thinking），具有自适应思考机制（根据问题难度自动开关思考），适用于通用场景，尤其在 非思考模式下效果大幅提升 。
deepseek-v3-250324：在数学推理和代码生成场景超越GPT-4.5，支持HTML前端任务的高可用性代码生成。
deepseek-r1-250528：通过强化学习优化参数生成，在多步骤函数调用场景中表现优异，需配合系统提示干预参数幻觉。（参考文末FAQ部分）
时延优先型（快速响应，效果相对宽松）
doubao-seed-1-6-flash-250615 ：适用于延迟敏感场景（如实时控制或高速调用），文本理解能力超上一代 lite 模型，且视觉理解比肩旗舰模型。
doubao-1-5-lite-32k-250115：平均响应时延降低40% ，适用于智能客服、实时控制等场景，支持并行函数调用。

使用流程

环境准备
调用方舟模型前，需先进行权限配置获取API Key并配置到环境变量。若通过火山引擎官方SDK或OpenAI SDK调用，需提前安装对应SDK，方舟已提供Go、Python、Java的SDK，便于快速集成模型服务。
环境配置参考:

获取 API Key 。

使用 Access Key 鉴权请参考Access Key 签名鉴权。
开通模型服务。

在模型列表获取所需 Model ID 。

通过 Endpoint ID 调用模型服务请参考获取 Endpoint ID（创建自定义推理接入点）。
安装及升级 SDK。


基本使用流程

步骤 1：定义函数
通过 tools 字段向模型描述可用函数，支持 JSON 格式，包含函数名称、描述、参数定义等信息。
定义工具函数

def get_current_weather(location, unit="摄氏度"):
    # 实际调用天气查询 API 的逻辑
    # 此处为示例，返回模拟的天气数据
    return f"{location}今天天气晴朗，温度 25 {unit}。"
代码中定义了一个名为 get_current_weather 的工具函数，用于获取指定地点的天气信息。
location：必需的参数，表示地点。
unit：可选参数，默认值为 摄氏度，表示温度单位。
函数内部目前只是返回模拟的天气数据，实际应用中需要调用真实的天气查询 API。
定义 Tools

{
  "type": "function",
  "function": {
    "name": "get_current_weather",
    "description": "获取指定地点的天气信息，支持摄氏度和华氏度两种单位",
    "parameters": {
      "type": "object",
      "properties": {
        "location": {
          "type": "string",
          "description": "地点的位置信息，例如北京、上海"
        },
        "unit": {
          "type": "string",
          "enum": ["摄氏度", "华氏度"],
          "description": "温度单位，可选值为摄氏度或华氏度"
        }
      },
      "required": ["location"]
    }
  }
}
tools 是一个列表，其中每个元素代表一个工具。这里定义了一个名为 get_current_weather 的函数。
type：工具的类型，这里是 function，表示这是一个函数调用工具。
function：包含函数的详细信息，如名称、描述和参数。
name：函数的名称，即 get_current_weather。
description：函数的描述，说明该函数用于获取指定地点的天气信息。
parameters：函数所需的参数，这里是一个对象，包含 location 和 unit 两个属性。
location：地点的位置信息，是一个字符串类型的参数。
unit：温度单位，是一个字符串类型的参数，可选值为 摄氏度 或 华氏度。
required：指定必需的参数，这里只有 location 是必需的。
更多关于函数 构造相关的规范和注意事项，请参见 附1：工具参数构造规范。

步骤 2：发起模型请求
在请求中包含用户问题和函数定义，模型会根据需求返回需要调用的函数及参数。

from volcenginesdkarkruntime import Ark

# 从环境变量中获取您的API KEY，配置方法见：https://www.volcengine.com/docs/82379/1399008
api_key = os.getenv('ARK_API_KEY')
# 初始化Ark客户端
client = Ark(
    api_key = api_key,
)

# 用户问题 
messages = [
    {"role": "user", "content": "北京今天的天气如何？"}
]
tools = [
    {
        # 参见步骤1中定义的tools
    }
]
# 发起模型请求
completion = client.chat.completions.create(
    # 替换 <MODEL> 为模型的Model ID
    model="<MODEL>",
    messages=messages,
    tools=tools
)

步骤 3：调用外部函数
根据模型返回的函数名称和参数，调用对应的外部函数具或 API，获取函数执行结果。

# 解析模型返回的函数调用信息
tool_call = completion.choices[0].message.tool_calls[0]
# 函数名称
tool_name = tool_call.function.name
# 如果判断需要调用查询天气函数，则运行查询天气函数
if tool_name == "get_current_weather":
    # 提取的用户参数
    arguments = json.loads(tool_call.function.arguments)
    # 调用函数
    tool_result = get_current_weather(**arguments)
tool_calls：获取模型调用的工具列表。
如果工具函数名称是 get_current_weather，则解析函数调用的参数并调用 get_current_weather 函数获取工具执行结果。

步骤 4：回填结果并获取最终回复
将工具执行结果以 role=tool 的消息形式回填给模型，模型根据结果生成最终回复。

messages.append(completion.choices[0].message)
messages.append({
    "role": "tool",
    "tool_call_id": tool_call.id,
    "content": tool_result
})

# 再次调用模型获取最终回复
final_completion = client.chat.completions.create(
    model="doubao-1-5-pro-32k-250115",
    messages=messages
)

print(final_completion.choices[0].message.content)

完整代码示例
Python - Arkiteck SDK
Python - Ark SDK
Java
Golang

（推荐）使用方舟智能体SDK Arkitect
from arkitect.core.component.context.context import Context
from enum import Enum
import asyncio
from pydantic import Field
def get_current_weather(location: str = Field(description="地点的位置信息，例如北京、上海"), unit: str=Field(description="温度单位, 可选值为摄氏度或华氏度")):
    """
    获取指定地点的天气信息
    """
    return f"{location}今天天气晴朗，温度 25 {unit}。"
async def chat_with_tool():
    ctx = Context(
            model="doubao-1-5-pro-32k-250115",
            tools=[
                get_current_weather
            ],  # 直接在这个list里传入你的所有python 方法作为tool，tool的描述会自动带给模型推理，tool的执行在ctx.completions.create 中会自动进行
        )
    await ctx.init()
    completion = await ctx.completions.create(messages=[
        {"role": "user", "content": "北京和上海今天的天气如何？"}
    ],stream =False)
    return completion
completion = asyncio.run(chat_with_tool())
print(completion.choices[0].message.content)


推荐配置与优化

新业务接入
推荐优选doubao-seed-1.6系列模型。
FC场景下，关闭 thinking 会提高效率，具体操作请参见开启关闭深度思考。
对速度有较高要求，可以选择 doubao-seed-1-6-flash-******模型。
准备评测集，在FC模型测试，看看准确率，以及业务预期上线准确率。
常规调优手段：
Functions的params、description等字段准确填写。 System prompt中不用再重复介绍函数，（可选）可以描述在何种情况下调用某函数
优化函数、参数的描述， 明确不同函数的边界情况； 避免歧义；增加示例等。
对模型进行sft（建议至少50条数据，模型越多、参数越多、情况越多，则所需要的数据越多），见精调优化。
速度优化： 对于简单无歧义的函数或参数，适当精简输入输出内容。

prompt最佳实践
原则： Treat LLM as a kid

能不用大模型完成的任务，就不要调用大模型，尽量代码完成。
和任务无关的信息，避免输入，避免信息干扰。
类别

问题

错误示例

改正后示例

函数

命名不规范、描述不规范

{
   "type": "function",
    "function": {
        "name": "GPT1",
        "description": "新建日程",
     }
}
{
   "type": "function",
    "function": {
        "name": "CreateEvent",
        "description": "当需要为用户新建日程时，此工具将创建日程，并返回日程ID",
     }
}
参数

避免不必要的复杂格式（或嵌套）

{
    "time": {
        "type": "object",
        "description": "事件时间",
        "properties": {
            "timestamp": {
                "description": "事件时间"
            }
        }
    }
}
{
    "time": {
        "type": "string",
        "description": "事件时间",
    }
}
避免固定值

{
    "time": {
        "type": "object",
        "description": "事件时间",
        "properties": {
            "timestamp": {
                "description": "固定传2024-01-01即可"
            }
        }
    }
}
既然参数值固定，删去该参数，由代码处理。

业务流程

尽量缩短LLM调用轮次

System prompt:

你正在与用户Alan沟通，你需要先查询用户ID，再通过ID创建日程……
System prompt:

你正在与用户Alan（ID=abc123）沟通，你可以通过ID创建日程……
歧义消解

System prompt:

可以通过ID查找用户，并获得用户的日程ID
这里两个ID未明确，模型可能会混用

System prompt:

每个用户具有唯一的用户ID；每个日程有对应的日程ID，两者独立的ID。
可以通过用户ID查找用户，并获得用户的所有日程ID

函数调用异常处理
JSON 格式容错机制：对于轻微不合法的 JSON 格式，可尝试使用 json-repair 库进行容错修复。

import json_repair

invalid_json = '{"location": "北京", "unit": "摄氏度"}'
valid_json = json_repair.loads(invalid_json)

需求澄清
需求澄清（确认需求），不依赖与FC，可独立使用。
可在 System prompt 中加入：

如果用户没有提供足够的信息来调用函数，请继续提问以确保收集到了足够的信息。
在调用函数之前，你必须总结用户的描述并向用户提供总结，询问他们是否需要进行任何修改。
......
在函数的 description 中加入：

函数参数除了提取a和b， 还应要求用户提供c、d、e、f和其他相关细节。
或在系统提示中加入参数校验逻辑，当模型生成的参数缺失时，引导模型重新生成完整的参数。

如果用户提供的信息缺少工具所需要的必填参数，你需要进一步追问让用户提供更多信息。

流式输出适配
从 Doubao-1.5 系列模型开始支持流式输出，逐步获取函数调用信息，提升响应效率。
详见Function Calling 流式输出适配。

def function_calling_stream():
    completion = client.chat.completions.create(
        model="doubao-1-5-pro-32k-250115",
        messages=messages,
        tools=tools,
        stream=True
    )
    for chunk in completion:
        if chunk.choices[0].delta.tool_calls:
            tool_call = chunk.choices[0].delta.tool_calls[0]
            print(f"名称：{tool_call.function.name}，参数：{tool_call.function.arguments}")

function_calling_stream()

多轮函数调用
当用户需求需要多次调用工具函数时，维护对话历史上下文，逐轮处理函数调用和结果回填。

示例流程
用户提问：“查询北京的天气，并将结果发送给张三”。
第一轮：模型调用 get_current_weather 工具获取北京天气。
第二轮：模型调用 send_message 工具将天气结果发送给张三。
第三轮：模型总结任务完成情况，返回最终回复。

代码示例
说明

多轮Function Calling：指用户query需要多次调用工具函数和大模型才能完成的情况， 是多轮对话的子集。

调用Response细节图：
Image


Golang
package main

import (
    "context"
    "encoding/json"
    "fmt"
    "os"
    "strings"

    "github.com/volcengine/volcengine-go-sdk/service/arkruntime"
    "github.com/volcengine/volcengine-go-sdk/service/arkruntime/model"
    "github.com/volcengine/volcengine-go-sdk/volcengine"
)

func main() {
    client := arkruntime.NewClientWithApiKey(
       os.Getenv("ARK_API_KEY"),
       arkruntime.WithBaseUrl("${BASE_URL}"),
    )

    fmt.Println("----- function call multiple rounds request -----")
    ctx := context.Background()
    // Step 1: send the conversation and available functions to the model
    req := model.CreateChatCompletionRequest{
       Model: "${Model_ID}",
       Messages: []*model.ChatCompletionMessage{
          {
             Role: model.ChatMessageRoleSystem,
             Content: &model.ChatCompletionMessageContent{
                StringValue: volcengine.String("你是豆包，是由字节跳动开发的 AI 人工智能助手"),
             },
          },
          {
             Role: model.ChatMessageRoleUser,
             Content: &model.ChatCompletionMessageContent{
                StringValue: volcengine.String("上海的天气怎么样？"),
             },
          },
       },
       Tools: []*model.Tool{
          {
             Type: model.ToolTypeFunction,
             Function: &model.FunctionDefinition{
                Name:        "get_current_weather",
                Description: "Get the current weather in a given location",
                Parameters: map[string]interface{}{
                   "type": "object",
                   "properties": map[string]interface{}{
                      "location": map[string]interface{}{
                         "type":        "string",
                         "description": "The city and state, e.g. Beijing",
                      },
                      "unit": map[string]interface{}{
                         "type":        "string",
                         "description": "枚举值有celsius、fahrenheit",
                      },
                   },
                   "required": []string{
                      "location",
                   },
                },
             },
          },
       },
    }
    resp, err := client.CreateChatCompletion(ctx, req)
    if err != nil {
       fmt.Printf("chat error: %v\n", err)
       return
    }
    // extend conversation with assistant's reply
    req.Messages = append(req.Messages, &resp.Choices[0].Message)
    
    // Step 2: check if the model wanted to call a function.
    // The model can choose to call one or more functions; if so,
    // the content will be a stringified JSON object adhering to
    // your custom schema (note: the model may hallucinate parameters).
    for _, toolCall := range resp.Choices[0].Message.ToolCalls {
       fmt.Println("calling function")
       fmt.Println("    id:", toolCall.ID)
       fmt.Println("    name:", toolCall.Function.Name)
       fmt.Println("    argument:", toolCall.Function.Arguments)
       functionResponse, err := CallAvailableFunctions(toolCall.Function.Name, toolCall.Function.Arguments)
       if err != nil {
          functionResponse = err.Error()
       }
       // extend conversation with function response
       req.Messages = append(req.Messages,
          &model.ChatCompletionMessage{
             Role:       model.ChatMessageRoleTool,
             ToolCallID: toolCall.ID,
             Content: &model.ChatCompletionMessageContent{
                StringValue: &functionResponse,
             },
          },
       )
    }
    // get a new response from the model where it can see the function response
    secondResp, err := client.CreateChatCompletion(ctx, req)
    if err != nil {
       fmt.Printf("second chat error: %v\n", err)
       return
    }
    fmt.Println("conversation", MustMarshal(req.Messages))
    fmt.Println("new message", MustMarshal(secondResp.Choices[0].Message))
}
func CallAvailableFunctions(name, arguments string) (string, error) {
    if name == "get_current_weather" {
       params := struct {
          Location string `json:"location"`
          Unit     string `json:"unit"`
       }{}
       if err := json.Unmarshal([]byte(arguments), &params); err != nil {
          return "", fmt.Errorf("failed to parse function call name=%s arguments=%s", name, arguments)
       }
       return GetCurrentWeather(params.Location, params.Unit), nil
    } else {
       return "", fmt.Errorf("got unavailable function name=%s arguments=%s", name, arguments)
    }
}

// GetCurrentWeather get the current weather in a given location.
// Example dummy function hard coded to return the same weather.
// In production, this could be your backend API or an external API
func GetCurrentWeather(location, unit string) string {
    if unit == "" {
       unit = "celsius"
    }
    switch strings.ToLower(location) {
    case "beijing":
       return `{"location": "Beijing", "temperature": "10", "unit": unit}`
    case "北京":
       return `{"location": "Beijing", "temperature": "10", "unit": unit}`
    case "shanghai":
       return `{"location": "Shanghai", "temperature": "23", "unit": unit}`
    case "上海":
       return `{"location": "Shanghai", "temperature": "23", "unit": unit}`
    default:
       return fmt.Sprintf(`{"location": %s, "temperature": "unknown"}`, location)
    }
}
func MustMarshal(v interface{}) string {
    b, _ := json.Marshal(v)
    return string(b)
}

Python
from volcenginesdkarkruntime import Ark
import time
client = Ark(
    base_url="${BASE_URL}",
)

print("----- function call multiple rounds request -----")
messages = [
    {
        "role": "system",
        "content": "你是豆包，是由字节跳动开发的 AI 人工智能助手",
    },
    {
        "role": "user",
        "content": "北京今天的天气",
    },
]
req = {
    "model": "${YOUR_ENDPOINT_ID}",
    "messages": messages,
    "temperature": 0.8,
    "tools": [
        {
            "type": "function",
            "function": {
                "name": "MusicPlayer",
                "description": """歌曲查询Plugin，当用户需要搜索某个歌手或者歌曲时使用此plugin，给定歌手，歌名等特征返回相关音乐。\n 例子1：query=想听孙燕姿的遇见， 输出{"artist":"孙燕姿","song_name":"遇见","description":""}""",
                "parameters": {
                    "properties": {
                        "artist": {"description": "表示歌手名字", "type": "string"},
                        "description": {
                            "description": "表示描述信息",
                            "type": "string",
                        },
                        "song_name": {
                            "description": "表示歌曲名字",
                            "type": "string",
                        },
                    },
                    "required": [],
                    "type": "object",
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "get_current_weather",
                "description": "",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "location": {
                            "type": "string",
                            "description": "地理位置，比如北京市",
                        },
                        "unit": {"type": "string", "description": "枚举值 [摄氏度,华氏度]"},
                    },
                    "required": ["location"],
                },
            },
        },
    ],
}

ts = time.time()
completion = client.chat.completions.create(**req)
if completion.choices[0].message.tool_calls:
    print(
        f"Bot [{time.time() - ts:.3f} s][Use FC]: ",
        completion.choices[0].message.tool_calls[0],
    )
    # ========== 补充函数调用的结果 =========
    req["messages"].extend(
        [
            completion.choices[0].message.dict(),
             {
                "role": "tool",
                "tool_call_id": completion.choices[0].message.tool_calls[0].id,
                "content": "北京天气晴，24~30度",  # 根据实际调用函数结果填写，最好用自然语言。
                "name": completion.choices[0].message.tool_calls[0].function.name,
            },
        ]
    )
    # 再请求一次模型，获得总结。 如不需要，也可以省略
    ts = time.time()
    completion = client.chat.completions.create(**req)
    print(
        f"Bot [{time.time() - ts:.3f} s][FC Summary]: ",
        completion.choices[0].message.content,
    )

Java
package com.volcengine.ark.runtime;

import com.volcengine.ark.runtime.model.completion.chat.*;
import com.volcengine.ark.runtime.service.ArkService;
import okhttp3.ConnectionPool;
import okhttp3.Dispatcher;

import java.util.*;
import java.util.concurrent.TimeUnit;

public class FunctionCallChatCompletionsExample {
    static String apiKey = System.getenv("ARK_API_KEY");
    static ConnectionPool connectionPool = new ConnectionPool(5, 1, TimeUnit.SECONDS);
    static Dispatcher dispatcher = new Dispatcher();
    static ArkService service = ArkService.builder().dispatcher(dispatcher).connectionPool(connectionPool).baseUrl("${BASE_URL}").apiKey(apiKey).build();

    public static void main(String[] args) {
        System.out.println("\n----- function call multiple rounds request -----");
        final List<ChatMessage> messages = new ArrayList<>();
        final ChatMessage userMessage = ChatMessage.builder().role(ChatMessageRole.USER).content("北京今天天气如何？").build();
        messages.add(userMessage);

        final List<ChatTool> tools = Arrays.asList(
                new ChatTool(
                        "function",
                        new ChatFunction.Builder()
                                .name("get_current_weather")
                                .description("获取给定地点的天气")
                                .parameters(new Weather(
                                        "object",
                                        new HashMap<String, Object>() {{
                                            put("location", new HashMap<String, String>() {{
                                                put("type", "string");
                                                put("description", "T地点的位置信息，比如北京");
                                            }});
                                            put("unit", new HashMap<String, Object>() {{
                                                put("type", "string");
                                                put("description", "枚举值有celsius、fahrenheit");
                                            }});
                                        }},
                                        Collections.singletonList("location")
                                ))
                                .build()
                )
        );

        ChatCompletionRequest chatCompletionRequest = ChatCompletionRequest.builder()
                .model("${YOUR_ENDPOINT_ID}")
                .messages(messages)
                .tools(tools)
                .build();

        ChatCompletionChoice choice = service.createChatCompletion(chatCompletionRequest).getChoices().get(0);
        messages.add(choice.getMessage());
        choice.getMessage().getToolCalls().forEach(
                toolCall -> {
                messages.add(ChatMessage.builder().role(ChatMessageRole.TOOL).toolCallId(toolCall.getId()).content("北京天气晴，24~30度").name(toolCall.getFunction().getName()).build());
        });
        ChatCompletionRequest chatCompletionRequest2 = ChatCompletionRequest.builder()
                .model("${YOUR_ENDPOINT_ID}")
                .messages(messages)
                .build();

        service.createChatCompletion(chatCompletionRequest2).getChoices().forEach(System.out::println);

        // shutdown service
        service.shutdownExecutor();
    }

    public static class Weather {
        public String type;
        public Map<String, Object> properties;
        public List<String> required;

        public Weather(String type, Map<String, Object> properties, List<String> required) {
            this.type = type;
            this.properties = properties;
            this.required = required;
        }

        public String getType() {
            return type;
        }

        public void setType(String type) {
            this.type = type;
        }

        public Map<String, Object> getProperties() {
            return properties;
        }

        public void setProperties(Map<String, Object> properties) {
            this.properties = properties;
        }

        public List<String> getRequired() {
            return required;
        }

        public void setRequired(List<String> required) {
            this.required = required;
        }
    }

}

响应示例
========== Round 1 ==========
user: 先查询北京的天气，如果是晴天微信发给Alan，否则发给Peter...

assistant [FC Response]:
name=GetCurrentWeather, args={"location": "\u5317\u4eac"} 
[elpase=2.607 s]
========== Round 2 ==========
tool: 北京今天20~24度，天气：阵雨。...

assistant [FC Response]:
name=SendMessage, args={"content": "\u4eca\u5929\u5317\u4eac\u7684\u5929\u6c14", "receiver": "Peter"} 
[elpase=3.492 s]
========== Round 3 ==========
tool: 成功发送微信消息至Peter...

assistant [Final Answer]:
好的，请问还有什么可以帮助您？ 
[elpase=0.659 s]

多轮输出注意事项
轮次输出顺序
触发函数调用时，系统先输出content给用户，再生成tool_calls并结束当前输出；当前轮次内容不可依赖工具结果，后续指令需待工具返回message后执行。

多轮输出响应完整性
严格遵循assistant（含tool_calls）→ tool（含message）→ assistant的顺序，禁止跳过tool message响应直接发送新的assistant消息。每次tool_calls需对应tool角色的 message（含成功/错误结果），缺失可能因prefill机制触发重复调用或流程中断。

精调优化
如果 Function Calling 效果未达预期，可通过精调（SFT）提升模型表现。
详情请参见模型精调概述。

精调场景
提高函数选择的准确性，确保模型在合适的时机调用正确的函数。
优化参数提取能力，使模型能够准确解析用户需求并生成正确的函数入参。
改善结果总结质量，让模型能够更自然、准确地总结工具执行结果。

精调样本格式
{
  "messages": [
    {
      "role": "system",
      "content": "你是豆包AI助手"
    },
    {
      "role": "user",
      "content": "把北京的天气发给李四"
    },
    {
      "role": "assistant",
      "content": "",
      "tool_calls": [
        {
          "type": "function",
          "function": {
            "name": "get_current_weather",
            "arguments": "{\"location\": \"北京\"}"
          }
        }
      ],
      "loss_weight": 1.0
    },
    {
      "role": "tool",
      "content": "北京今天晴，25摄氏度"
    },
    {
      "role": "assistant",
      "content": "",
      "tool_calls": [
        {
          "type": "function",
          "function": {
            "name": "send_message",
            "arguments": "{\"receiver\": \"李四\", \"content\": \"北京今天晴，25摄氏度\"}"
          }
        }
      ],
      "loss_weight": 1.0
    },
    {
      "role": "tool",
      "content": "消息发送成功"
    },
    {
      "role": "assistant",
      "content": "已将北京的天气信息发送给李四"
    }
  ],
  "tools": [
    {
      "type": "function",
      "function": {
        "name": "get_current_weather",
        "description": "获取指定地点的天气",
        "parameters": {
          "type": "object",
          "properties": {
            "location": {"type": "string", "description": "地点的位置信息"}
          },
          "required": ["location"]
        }
      }
    }
  ]
}

常见问题

Q：FC & MCP 的核心区别是什么，使用时如何选型？
核心区别与典型使用场景

维度

FC（Function Calling）

MCP（Model Context Protocol）

本质

模型调用外部工具 / 函数的能力（功能扩展）

定义模型与外部系统交互时的上下文管理协议（流程规范）

目标

弥补模型自身能力不足（如计算、数据查询、操作执行）

标准化交互过程中上下文的传递、解析与状态维护

核心作用

实现模型与外部工具的 “能力集成”

确保多轮交互中上下文（如对话历史、参数、状态）的一致性

协议标准

厂商自定义格式（如 OpenAI 的 JSON 参数结构）

强制遵循 JSON-RPC 2.0 标准，强调协议统一性

架构

直接集成于模型 API，用户定义函数后由模型触发调用

客户端 - 服务器模式，分离 MCP Host（客户端）与 MCP Server（服务端）

上下文管理

单次请求 - 响应模式，上下文依赖需开发者自行处理

支持多轮对话、历史状态维护，适用于长序列依赖任务

典型使用场景

外部数据调用与系统操作（如天气查询、复杂运算）；示例：调用天气 API 回复 “东京今日气温”

多轮对话与跨系统上下文管理（如订餐流程、客服对话）；示例：连贯处理订餐菜品与配送地址

两者之间的关系

互补而非互斥：
MCP 可能在流程中包含 FC 的调用逻辑（如定义何时、如何触发函数调用）
FC 的输入输出需遵循 MCP 的上下文规范（如参数格式、返回值解析规则）
分层协作：
MCP 解决连接问题：标准化协议打通数据孤岛，提供基础设施（如整合用户订单数据）。
FC 解决执行问题：在协议层之上调用具体函数完成任务（如调用库存 API 生成补货建议）。
架构定位：FC 是能力接口，MCP 是交互框架，二者常结合使用以构建复杂应用（如智能助手同时需要调用工具和管理多轮对话状态）。
References

MCP 官方协议规范（草案）：明确协议核心架构、JSON - RPC 消息格式、状态管理机制与安全策略，是接口设计的权威参考。Model Context Protocol Specification
MCP 社区与生态发展：介绍 MCP 发展规划，涵盖远程连接支持、沙箱安全机制及多模态扩展等发展计划。MCP Development Roadmap

Q：Deepseek R1 模型是否支持并行函数调用？
A：暂不支持 parallel_tool_calls 控制字段，该模型默认采用自动触发并行调用机制，开发者无需额外配置即可实现多工具并行调用。

Q：如何处理 Deepseek R1 的参数幻觉问题？
A：该模型在复杂参数解析时可能出现嵌套调用异常（如 get_weather:{city: get_location()}），建议通过以下方式干预：

在 system prompt 中明确要求分步调用（如“请先调用定位函数，再调用天气查询函数”）
使用 JSON Schema 校验强制参数格式

Q：如何判断模型是否需要调用函数？
A：模型会根据用户问题和工具定义自主判断，若返回结果中包含 tool_calls 字段，则表示需要调用工具；若 content 字段有直接回复，则无需调用工具。

Q：支持并行调用多个函数吗？
A：支持并行函数调用，通过设置 parallel_tool_calls 参数为 true，模型可同时返回多个函数调用信息，提高处理效率。

Q：为什么模型返回的工具参数存在幻觉？
A：这是大模型常见的问题，可通过精调（SFT）优化模型的参数生成能力，或在系统提示中明确参数的格式和范围，减少幻觉现象。
部分模型（特别是Deepseek R1）存在一些参数幻觉问题。 如预期先调用get_location获得城市，再调用get_weather查询，R1模型有概率直接返回get_weather:{city: get_location()} 这种嵌套调用， 请在system prompt中进行干预解决，分步完成调用。

Q：如何处理函数调用失败的情况？
A：将工具失败信息以 role=tool 的消息回填给模型，模型会根据错误信息生成相应的回复，例如“抱歉，函数调用失败，请稍后重试。”
通过以上优化，开发者能够更高效地使用 Function Calling 功能，实现大模型与外部工具的深度整合，快速构建智能应用。


附1：工具函数参数构造规范
为确保模型正确调用工具功能，需按以下规范构造 tools 对象，遵循 JSON Schema 标准。
本文主要讲解如何构造 Function Calling 工具，关于工具函数的使用请参考基本使用流程。

总体结构
{
  "type": "function",
  "function": {
    "name": "...",          // 函数名称（小写+下划线）
    "description": "...",   // 功能描述
    "parameters": { ... }   // 参数定义（JSON Schema格式）
  }
}
type：工具的类型，这里是固定值 function，表示这是一个函数调用工具。
function：含函数名称、描述和参数等详细配置。

字段解释

function 字段
字段

类型

是否必填

说明

name

string

是

函数名称，唯一标识，建议使用小写加下划线

description

string

是

函数作用的描述

parameters

object

是

函数参数定义，需要符合 JSON Schema 格式


parameters 字段
parameters 须为符合 JSON Schema 格式的对象：

{
  "type": "object",
  "properties": {
    "参数名": {
      "type": "string | number | boolean | object | array",
      "description": "参数说明"
    }
  },
  "required": ["必填参数"]
}
type：必须是 "object"。
properties：列出支持的所有参数名及其类型。
参数名须为英文字符串，且不能重复。
参数type需遵循json规范，支持类型包括string、number、boolean、integer、object、array。
required：指定函数中必填的参数名。
其它参数根据type的不同稍有区别，详情请参见下表。
type类型

示例

string、integer、number、boolean

略

object （对象）

description：简要说明
properties 描述该对象所有属性
required 描述必填属性
示例1: 查询特点用户画像（根据年龄、性别、婚姻状况等）
"person": {
    "type": "object",
    "description": "个人特征",
    "properties": {
        "age": {"type": "integer", "description": "年龄"},
        "gender": {"type": "string", "description": "性别"},
        "married": {"type": "boolean", "description": "是否已婚"}
    },
    "required": ["age"],
}
array （列表）

description:简要说明
"items": {"type": ITEM_TYPE}来表达数组元素的数据类型
示例1：文本数组，若干个网页链接
"url": {
    "type": "array",
    "description": "需要解析网页链接,最多3个",
    "items": {"type": "string"}
示例2： 二维数组
"matrix": {
    "type": "array",
    "description": "需要计算的二维矩阵",
    "items": {"type": "array", "items": {"type": "number"}},
}
示例3: 通过array来实现多选
"grade": {
    "description": "年级, 支持多选",
    "type": "array",
    "items": {
        "type": "string",
        "description": """枚举值有
            "一年级",
            "二年级",
            "三年级",
            "四年级",
            "五年级",
            "六年级"。 """,
    },
}

完整示例
{
  "type": "function",
  "function": {
    "name": "get_weather",
    "description": "获取指定位置的天气信息",
    "parameters": {
      "type": "object",
      "properties": {
        "location": {
          "type": "string",
          "description": "城市和国家，例如：北京，中国"
        }
      },
      "required": ["location"]
    }
  }
}

注意事项
大小写敏感：所有字段名、参数名严格区分大小写（建议统一用小写）。
中文处理：字段名用英文，中文说明置于 description 中（如 location 的描述为 “城市和国家”）。
Schema 合规性：parameters 必须是有效的 JSON Schema 对象，可通过JSON Schema 校验工具验证。

最佳实践
工具描述核心准则
详细说明工具功能、适用场景（及禁用场景）、参数含义与影响、限制条件（如输入长度限制），单工具描述建议3-4句。
优先完善功能、参数等基础描述，示例仅作为补充（推理模型需谨慎添加）。
函数设计要点
命名与参数：函数名直观（如parse_product_info），参数说明包含格式（如city: string）和业务含义（如“目标城市拼音全称”），明确输出定义（如“返回JSON格式天气数据”）。
系统提示：通过提示指定调用条件（如“用户询问商品详情时触发get_product_detail”）。
工程化设计：
使用枚举类型（如StatusEnum）避免无效参数，确保逻辑直观（最小惊讶原则）。
确保仅凭文档描述，人类可正确调用函数（补充潜在疑问解答）。
调用优化：
已知参数通过火山方舟代码能力隐式传递（如submit_order无需重复声明user_id）。
合并固定流程函数（如query_location与mark_location整合为query_and_mark_location）。
数量与性能：控制函数数量≤20个，通过火山方舟调试工具迭代函数模式（Schema），复杂场景可使用微调能力提升准确率。
