# Deep Research 前端使用指南

## 概述

Deep Research 现在提供了一个完整的 Web 界面，支持文档管理、向量搜索、证据链可视化、系统监控等功能。

## 功能特性

### 🏠 主界面
- **对话界面**: 传统的聊天界面，支持与AI模型对话
- **控制台界面**: 新的管理界面，集成所有高级功能

### 📁 文档管理
- **文件上传**: 支持PDF、Word、TXT、Markdown等格式
- **处理状态监控**: 实时查看文档处理进度
- **批量操作**: 支持批量上传和管理文档
- **搜索过滤**: 按状态、类型等条件过滤文档

### 🔍 文档搜索
- **向量搜索**: 基于语义的智能搜索
- **实时结果**: 搜索结果实时显示
- **相关性评分**: 显示搜索结果的相关性分数
- **证据链集成**: 可查看搜索结果的证据来源

### 📋 证据链可视化
- **证据追踪**: 显示搜索和推理过程中的证据来源
- **可信度评分**: 显示证据的可信度和质量评分
- **验证机制**: 支持用户对证据进行验证和标记
- **来源链接**: 直接跳转到原始来源

### 📊 系统监控
- **健康检查**: 实时显示系统各组件健康状态
- **性能指标**: 显示请求响应时间、错误率等指标
- **资源使用**: 显示CPU、内存、磁盘使用情况
- **统计数据**: 显示文档数量、搜索次数等统计信息

## 快速开始

### 1. 安装依赖

```bash
cd vue
npm install
```

### 2. 配置环境变量

创建 `.env` 文件：

```bash
VUE_APP_API_BASE_URL=http://localhost:8000/api
```

### 3. 启动开发服务器

```bash
npm run dev
```

### 4. 构建生产版本

```bash
npm run build
```

## 使用指南

### 切换界面

1. 点击顶部导航栏的"对话"按钮进入聊天界面
2. 点击"控制台"按钮进入管理界面

### 上传文档

1. 在控制台界面点击"文档管理"面板
2. 点击"上传文档"按钮选择文件
3. 支持的文件格式：PDF、DOCX、DOC、TXT、MD
4. 上传后可实时查看处理进度

### 搜索文档

1. 在"文档搜索"面板输入关键词
2. 可选择是否包含证据链
3. 点击搜索按钮查看结果
4. 点击结果项可查看详细信息

### 查看证据链

1. 在"证据链"面板查看当前对话的证据
2. 可以标记证据为已验证或已使用
3. 查看证据的来源链接和评分

### 系统监控

1. 在"系统监控"面板查看系统状态
2. 包含健康检查、性能指标、系统信息
3. 支持自动刷新功能

## 技术栈

- **Vue 3**: 现代化的前端框架
- **Pinia**: 状态管理库
- **CSS Variables**: 主题系统
- **ES6 Modules**: 模块化开发
- **响应式设计**: 支持移动端和桌面端

## 组件结构

```
src/
├── components/
│   ├── App.vue              # 主应用组件
│   ├── Dashboard.vue        # 控制台主界面
│   ├── DocumentManager.vue  # 文档管理组件
│   ├── DocumentSearch.vue   # 文档搜索组件
│   ├── EvidenceChain.vue    # 证据链组件
│   ├── SystemMonitor.vue    # 系统监控组件
│   ├── ChatContainer.vue    # 聊天容器
│   └── ...
├── services/
│   └── api.js              # API服务层
├── store/
│   └── index.js            # Pinia状态管理
├── assets/
│   ├── theme.css           # 主题样式
│   └── icons.css           # 图标样式
└── main.js                 # 应用入口
```

## API 接口

前端通过以下API接口与后端通信：

### 健康检查
- `GET /api/health` - 基础健康检查
- `GET /api/health/detailed` - 详细健康检查
- `GET /api/health/metrics` - 获取监控指标

### 文档管理
- `POST /api/rag/upload-document` - 上传文档
- `GET /api/rag/documents` - 获取文档列表
- `GET /api/rag/document/{jobId}` - 获取文档状态
- `DELETE /api/rag/document/{jobId}` - 删除文档

### 搜索功能
- `GET /api/rag/search` - 向量搜索文档

### 证据链
- `GET /api/evidence/conversation/{id}` - 获取对话证据
- `PUT /api/evidence/{id}/mark_used` - 标记证据使用状态

## 样式主题

支持明暗两种主题，通过CSS变量实现：

```css
:root {
  --primary-bg: #ffffff;
  --secondary-bg: #f8f9fa;
  --text-primary: #1f2937;
  --text-secondary: #6b7280;
  --accent-color: #3b82f6;
  --border-color: #e5e7eb;
  --success-color: #10b981;
  --error-color: #ef4444;
  --warning-color: #f59e0b;
}
```

## 浏览器支持

- Chrome 70+
- Firefox 70+
- Safari 12+
- Edge 79+

## 故障排除

### 常见问题

1. **API请求失败**
   - 检查后端服务是否运行
   - 确认API_BASE_URL配置正确
   - 查看浏览器控制台错误信息

2. **文件上传失败**
   - 检查文件大小是否超过限制
   - 确认文件格式是否支持
   - 查看网络连接状态

3. **样式显示异常**
   - 确认CSS变量定义完整
   - 检查主题切换逻辑
   - 清除浏览器缓存

### 调试模式

在开发环境中，可以通过以下方式启用调试：

```javascript
// 在浏览器控制台中
localStorage.setItem('debug', 'true');
location.reload();
```

## 贡献指南

1. Fork 项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

## 许可证

本项目采用 MIT 许可证。
