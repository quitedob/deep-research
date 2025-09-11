# 前端配置文件示例

## .env 文件配置

创建 `.env` 文件并配置以下变量：

```bash
# API 基础URL
VUE_APP_API_BASE_URL=http://localhost:8000/api

# 应用配置
VUE_APP_NAME=Deep Research
VUE_APP_VERSION=1.0.0

# 开发配置
VUE_APP_DEBUG=true

# 功能开关
VUE_APP_ENABLE_HEALTH_CHECK=true
VUE_APP_ENABLE_SYSTEM_MONITOR=true
VUE_APP_ENABLE_DOCUMENT_SEARCH=true
VUE_APP_ENABLE_EVIDENCE_CHAIN=true

# UI 配置
VUE_APP_DEFAULT_THEME=dark
VUE_APP_MAX_UPLOAD_SIZE=52428800
VUE_APP_SUPPORTED_FILE_TYPES=.pdf,.docx,.doc,.txt,.md

# 监控配置
VUE_APP_HEALTH_CHECK_INTERVAL=30000
VUE_APP_AUTO_REFRESH_ENABLED=true
```

## 配置说明

### API 配置
- `VUE_APP_API_BASE_URL`: 后端API的基础URL
- 默认值: `http://localhost:8000/api`

### 功能开关
- `VUE_APP_ENABLE_HEALTH_CHECK`: 启用健康检查功能
- `VUE_APP_ENABLE_SYSTEM_MONITOR`: 启用系统监控功能
- `VUE_APP_ENABLE_DOCUMENT_SEARCH`: 启用文档搜索功能
- `VUE_APP_ENABLE_EVIDENCE_CHAIN`: 启用证据链可视化功能

### UI 配置
- `VUE_APP_DEFAULT_THEME`: 默认主题 ('dark' 或 'light')
- `VUE_APP_MAX_UPLOAD_SIZE`: 最大文件上传大小（字节）
- `VUE_APP_SUPPORTED_FILE_TYPES`: 支持的文件类型（用逗号分隔）

### 监控配置
- `VUE_APP_HEALTH_CHECK_INTERVAL`: 健康检查间隔时间（毫秒）
- `VUE_APP_AUTO_REFRESH_ENABLED`: 是否启用自动刷新
