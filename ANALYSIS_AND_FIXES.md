# 日志问题分析与修复方案

## 问题分析

### 1. 报告生成错误
**错误信息**: `TypeError: can only concatenate str (not "list") to str`
**位置**: `src/core/agentscope/research_agent.py:778`

**原因**: 
- AgentScope 的 `Msg.content` 可能是 `list[ContentBlock]` 类型
- 代码尝试将列表直接与字符串拼接

**已修复**: ✅
- 添加了类型检查和转换逻辑
- 正确处理列表类型的 content，提取文本内容

### 2. 前端未收到最终报告
**问题**: 研究已完成并生成报告，但前端没有收到

**原因分析**:
1. 报告已在 `conduct_research` 方法中生成
2. 报告存储在 `self.research_result` 中
3. `export_session_data` 方法正确导出了报告
4. SSE 流正确调用了 `format_final_report` 和 `generate_full_report_text`

**流程**:
```
conduct_research() 
  → _generate_research_report() [生成报告]
  → self.research_result = {..., "report": report} [存储]
  → export_session_data() [导出，包含 report 字段]
  → SSE: format_final_report() [格式化]
  → SSE: generate_full_report_text() [生成完整文本]
  → 推送给前端
```

## AgentScope 输出结构

根据搜索结果和代码分析：

### Msg 对象结构
```python
class Msg:
    name: str  # 发送者名称
    role: Literal["user", "assistant", "system"]  # 角色
    content: str | list[ContentBlock]  # 内容（可能是字符串或列表）
    metadata: dict  # 元数据
    timestamp: str  # 时间戳
```

### reply 方法返回值
- AgentScope 的 `reply()` 方法返回 `Msg` 对象
- `Msg.content` 可能是：
  - 字符串：直接的文本内容
  - 列表：`list[ContentBlock]`，每个元素可能包含 `text` 字段

## 修复内容

### 1. 修复报告生成中的类型错误 ✅

**文件**: `src/core/agentscope/research_agent.py`

**修改**:
```python
# ✅ 处理 content 可能是列表的情况
if isinstance(report_content, list):
    # 提取所有文本内容
    text_parts = []
    for item in report_content:
        if isinstance(item, dict) and 'text' in item:
            text_parts.append(str(item['text']))
        elif hasattr(item, 'text'):
            text_parts.append(str(item.text))
        else:
            text_parts.append(str(item))
    report_content = '\n'.join(text_parts)
elif not isinstance(report_content, str):
    report_content = str(report_content)
```

### 2. 确保报告正确存储和导出 ✅

**已验证**:
- `conduct_research()` 正确生成并存储报告到 `self.research_result`
- `export_session_data()` 正确导出报告字段
- SSE 流正确处理和推送报告

## 前端接收流程

### SSE 事件类型

1. **connected**: 连接成功
```json
{
  "type": "connected",
  "session_id": "xxx"
}
```

2. **status_update**: 状态更新
```json
{
  "type": "status_update",
  "status": "in_progress",
  "data": {...}
}
```

3. **completed**: 研究完成（包含完整报告）
```json
{
  "type": "completed",
  "status": "completed",
  "data": {
    "report_text": "# 完整的 Markdown 报告...",
    "session_id": "xxx"
  }
}
```

4. **failed**: 研究失败
```json
{
  "type": "failed",
  "status": "failed",
  "error": "错误信息"
}
```

## 前端需要做的修改

### 当前问题
前端可能在错误地接收：
- 工具调用信息
- 搜索结果
- 中间过程数据

而不是最终的完整报告。

### 建议修改

```javascript
// 前端 SSE 监听代码
const eventSource = new EventSource(`/api/research/stream/${sessionId}`);

eventSource.onmessage = (event) => {
  const data = JSON.parse(event.data);
  
  switch(data.type) {
    case 'connected':
      console.log('已连接到研究会话');
      break;
      
    case 'status_update':
      // 更新进度条和状态
      updateProgress(data.status, data.data);
      break;
      
    case 'completed':
      // ✅ 显示最终报告
      const reportText = data.data.report_text;
      displayFinalReport(reportText);
      eventSource.close();
      break;
      
    case 'failed':
      // 显示错误
      displayError(data.error);
      eventSource.close();
      break;
  }
};
```

## 验证步骤

1. ✅ 修复了 `_generate_research_report` 中的类型错误
2. ✅ 确认报告正确存储在 `self.research_result`
3. ✅ 确认 `export_session_data` 包含报告字段
4. ✅ 确认 SSE 流正确格式化和推送报告

## 总结

**后端修复**:
- ✅ 修复了 AgentScope Msg.content 列表类型处理
- ✅ 确保报告生成和存储流程正确
- ✅ SSE 流正确推送完整报告

**前端需要**:
- 正确监听 SSE 的 `completed` 事件
- 从 `data.data.report_text` 获取完整报告
- 不要显示中间的工具调用和搜索结果（这些是内部过程）
