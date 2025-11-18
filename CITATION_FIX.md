# 引用/证据链修复方案

## 问题分析

当前问题：
1. ✅ 后端已经生成完整报告（包含参考文献）
2. ✅ 前端可以接收并显示报告
3. ❌ 参考文献列表应该作为证据链（evidence）展示，而不是放在报告正文中
4. ❌ 前端的 `EvidenceChain` 组件和 `MessageItem` 的证据展示功能未被使用

## 当前数据流

```
后端生成报告
  ↓
报告包含参考文献（在正文中）
  ↓
SSE 推送 report_text
  ↓
前端显示完整报告（包括参考文献）
  ↓
❌ 证据链组件未被使用
```

## 期望数据流

```
后端生成报告
  ↓
分离报告正文和引用数据
  ↓
SSE 推送:
  - report_text: 报告正文（不含参考文献）
  - citations: 引用数据数组
  - evidence: 证据链数据
  ↓
前端接收:
  - 显示报告正文
  - 通过 MessageItem 的证据展示功能显示引用
  ↓
✅ 用户可以点击展开查看证据链
```

## 数据结构

### 后端 SSE 推送格式

```json
{
  "type": "completed",
  "status": "completed",
  "data": {
    "report_text": "# 报告正文（不含参考文献）...",
    "session_id": "xxx",
    "metadata": {
      "type": "research",
      "session_id": "xxx",
      "evidence": [
        {
          "id": 1,
          "source_type": "web",
          "source_title": "Wikipedia - 白银贸易",
          "source_url": "https://zh.wikipedia.org/wiki/白银贸易",
          "content": "引用内容摘要...",
          "relevance_score": 0.95,
          "confidence_score": 0.90
        }
      ],
      "citations": [
        {
          "title": "白银贸易",
          "authors": ["Wikipedia"],
          "source_url": "https://zh.wikipedia.org/wiki/白银贸易",
          "publication_year": 2025
        }
      ]
    }
  }
}
```

### 前端 MessageItem 期望格式

```javascript
message = {
  role: 'assistant',
  content: '报告正文...',
  metadata: {
    type: 'research',
    session_id: 'xxx',
    evidence: [
      {
        source_type: 'web',
        source_title: '来源标题',
        source_url: 'https://...',
        content: '引用内容',
        relevance_score: 0.95,
        confidence_score: 0.90
      }
    ]
  }
}
```

## 修复步骤

### 1. 后端修改

#### 1.1 修改 `export_session_data` 方法

在 `src/services/agentscope_research_service.py` 中，确保导出数据包含引用信息：

```python
return {
    "session_info": {...},
    "findings": serialized_findings,
    "citations": serialized_citations,  # ✅ 已有
    "memory": agent_data.get("short_memory", []),
    "report": report,
    "tools_used": agent_data.get("tools_used", []),
    "exported_at": datetime.now().isoformat()
}
```

#### 1.2 修改 SSE 推送逻辑

在 `src/api/deep_research.py` 的 `stream_research_progress` 方法中：

```python
# 研究完成，推送最终报告
if current_status == "completed":
    export_data = await research_service.export_session_data(session_id)
    
    if export_data:
        # 生成报告（不含参考文献）
        formatted_report = await research_service.format_final_report(
            session_id,
            export_data
        )
        
        full_report_text = research_service.generate_full_report_text(formatted_report)
        
        # ✅ 转换引用数据为前端格式
        citations = export_data.get("citations", [])
        evidence_list = []
        for idx, citation in enumerate(citations):
            evidence_list.append({
                "id": idx + 1,
                "source_type": "web" if "wikipedia" in citation.get("source_url", "").lower() else "document",
                "source_title": citation.get("title", "未知来源"),
                "source_url": citation.get("source_url", ""),
                "content": f"引用自: {citation.get('title', '')}",
                "relevance_score": 0.95,
                "confidence_score": 0.90
            })
        
        # 推送完成事件
        final_event = {
            "type": "completed",
            "status": "completed",
            "data": {
                "report_text": full_report_text,
                "session_id": session_id,
                "metadata": {
                    "type": "research",
                    "session_id": session_id,
                    "evidence": evidence_list,  # ✅ 添加证据链
                    "citations": citations
                }
            }
        }
        yield f"data: {json.dumps(final_event, ensure_ascii=False, default=str)}\n\n"
```

### 2. 前端修改

#### 2.1 修改 Home.vue

在接收 SSE 事件时，保存 metadata：

```javascript
else if (data.type === 'completed') {
  console.log('✓ 研究完成，收到最终报告');
  eventSource.close();
  
  const responseData = data.data;
  const reportText = responseData?.report_text || '研究完成，但报告为空。';
  const metadata = responseData?.metadata || {};  // ✅ 获取 metadata
  
  console.log('报告长度:', reportText.length, '字符');
  console.log('证据数量:', metadata.evidence?.length || 0);
  
  chatStore.updateMessageContent({
    messageId: assistantMessageId,
    contentChunk: reportText,
    metadata: metadata  // ✅ 传递 metadata
  });
  
  chatStore.setTypingStatus(false);
  chatStore.setResearchMode(false, null);
}
```

#### 2.2 修改 ResearchButton.vue

同样保存 metadata：

```javascript
case 'completed':
  console.log('✓ 研究完成，收到最终报告');
  const reportText = data.data?.report_text || '研究完成，但报告为空。';
  const metadata = data.data?.metadata || {};  // ✅ 获取 metadata
  completeResearch(reportText, metadata);  // ✅ 传递 metadata
  break;

// 修改 completeResearch 函数
const completeResearch = (report, metadata = {}) => {
  isResearching.value = false;
  researchProgress.value = '✓ 研究完成！';
  
  if (researchEventSource.value) {
    researchEventSource.value.close();
    researchEventSource.value = null;
  }
  
  // 将研究报告添加到聊天
  chatStore.addMessage({
    role: 'assistant',
    content: report,
    timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    type: 'research_report',
    metadata: metadata  // ✅ 添加 metadata
  });
  
  emit('research-complete', report);
  
  setTimeout(() => {
    researchProgress.value = '';
  }, 3000);
};
```

### 3. 报告生成修改

#### 3.1 从报告中移除参考文献部分

在 `src/core/agentscope/research_agent.py` 的 `_generate_research_report` 方法中，生成报告时不包含参考文献：

```python
prompt = f"""请基于以下研究发现，生成一份完整的研究报告。

研究主题: {query}

研究发现:
{findings_text}

请生成一份结构化的研究报告，包含以下部分：
1. 执行摘要（200-300字）
2. 背景介绍
3. 主要发现（分点详细说明）
4. 深入分析
5. 结论与建议

⚠️ 注意：不要包含参考文献列表，引用信息将单独展示

要求：
- 使用 Markdown 格式
- 内容要专业、准确、有深度
- 综合所有发现，形成连贯的叙述
- 突出重点和关键信息
- 总字数控制在 2000-3000 字"""
```

## 最终效果

### 用户视角

1. 用户发起研究："今日银价"
2. 系统显示进度："🔍 正在进行深度研究..."
3. 研究完成，显示报告正文（不含参考文献）
4. 报告下方显示："研究证据 (7)" 按钮
5. 用户点击展开，看到：
   ```
   ▼ 研究证据 (7)
   
   1. [Web] Wikipedia - 白银贸易
      相关性: 95%
      查看来源 →
   
   2. [Web] 今日银价搜索结果
      相关性: 90%
      查看来源 →
   
   ...
   ```

### 优势

1. ✅ 报告正文更简洁，专注于内容
2. ✅ 引用信息结构化展示，易于查看
3. ✅ 用户可以选择性查看证据链
4. ✅ 符合学术规范（正文与引用分离）
5. ✅ 提升用户体验（类似 Google Gemini 的引用展示）

## 实施优先级

### 高优先级（必须）
1. ✅ 后端 SSE 推送包含 metadata.evidence
2. ✅ 前端接收并保存 metadata
3. ✅ MessageItem 正确显示证据链

### 中优先级（建议）
1. 从报告生成中移除参考文献部分
2. 优化证据链数据格式
3. 添加证据来源图标

### 低优先级（可选）
1. 证据链的高级过滤功能
2. 证据可信度评分
3. 证据内容预览

## 测试验证

### 测试步骤
1. 启动研究："今日银价"
2. 等待研究完成
3. 检查报告是否显示
4. 检查是否有"研究证据"按钮
5. 点击展开，查看证据列表
6. 点击"查看来源"，验证链接

### 预期结果
- ✅ 报告正文清晰，无参考文献列表
- ✅ 证据链按钮显示正确数量
- ✅ 证据列表格式正确
- ✅ 来源链接可点击

## 总结

这个修复方案将：
1. 分离报告正文和引用信息
2. 通过 metadata 传递证据链数据
3. 利用现有的 MessageItem 证据展示功能
4. 提供更好的用户体验

**关键点**：后端需要在 SSE 推送时包含 `metadata.evidence` 数组，前端需要正确接收并传递给 MessageItem 组件。
