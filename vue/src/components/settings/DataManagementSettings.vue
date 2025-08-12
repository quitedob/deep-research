<template>
  <div class="settings-section">
    <h3>数据管理</h3>
    <div class="setting-item">
      <span>已归档的聊天</span>
      <button class="action-button">管理</button>
    </div>
    <div class="setting-item">
      <span>归档所有聊天</span>
      <button class="action-button">全部归档</button>
    </div>
    <div class="setting-item">
      <span>删除所有聊天</span>
      <button class="action-button danger">全部删除</button>
    </div>
  </div>
</template>

<style scoped>
/* 共享 .setting-item 和 h3 样式 */
.settings-section h3 { font-size: 18px; margin-bottom: 20px; color: var(--text-primary); }
.setting-item { display: flex; justify-content: space-between; align-items: center; padding: 15px 0; border-bottom: 1px solid var(--border-color); }
.setting-item:last-child { border-bottom: none; }
.setting-item span { font-size: 15px; }

.action-button {
  padding: 8px 16px;
  border: 1px solid var(--border-color);
  background-color: var(--secondary-bg);
  color: var(--text-primary);
  border-radius: 6px;
  cursor: pointer;
}
.action-button:hover {
  background-color: var(--hover-bg);
}
.action-button.danger {
  background-color: #ef4444; /* 红色 */
  color: white;
  border-color: #ef4444;
}
.action-button.danger:hover {
  background-color: #dc2626;
}
</style>