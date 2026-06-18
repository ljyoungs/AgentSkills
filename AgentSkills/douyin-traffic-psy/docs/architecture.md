# 技术架构说明

## 整体架构

```
用户对话
   │
   ▼
WorkBuddy Agent (AI)
   │ 调用
   ▼
Chrome DevTools MCP
   │ CDP协议
   ▼
Chrome 浏览器 (已登录抖音)
   │
   ▼
抖音页面 evaluate_script 注入
   │
   ├─ 搜索 → 热度排序 → 视频列表提取
   ├─ 导航视频详情页
   ├─ 滚动评论区 (WheelEvent)
   ├─ 提取评论 (CSS选择器 + DOM遍历)
   └─ 关键词匹配 → 可选：回复
```

## 核心设计原则

### 零快照架构
所有页面数据通过 `evaluate_script` 直接在页面 JS 上下文执行提取，**不使用截图**。
- 优势：Token 消耗极低（截图约 500-1000 token/张，JS 提取约 50-100 token）
- 速度快：无图片编码/解码开销

### 选择器策略（容错多层）
```javascript
// 优先 data-e2e 属性（官方测试标记，最稳定）
document.querySelector('[data-e2e="comment-item"]')
// 次选 class 模糊匹配
document.querySelector('[class*="commentItem"]')
// 兜底 DOM 结构
document.querySelector('.comment-mainContent > div > div')
```

### 状态机流程
```
INIT → SEARCH → SORT → EXTRACT_LIST → [FOR EACH VIDEO]
  → NAVIGATE → WAIT_LOAD → SCROLL_COMMENTS → EXTRACT_COMMENTS
  → FILTER_KEYWORDS → [IF REPLY_ENABLED] REPLY → RATE_LIMIT
```

## 文件职责

| 文件 | 职责 |
|------|------|
| `douyin_tools.js` | 页面 JS 工具集（搜索/排序/提取/回复），在浏览器上下文执行 |
| `config_manager.py` | 配置 CRUD，行业模板，导入导出，统计面板 |
| `setup_wizard.py` | 环境诊断（MCP连通/浏览器状态/依赖检查） |

## 风控机制

- **日限额**：`max_daily_total_replies` 全局上限
- **间隔控制**：每次回复后随机等待 `reply_interval_seconds ± 随机扰动`
- **验证码检测**：检测页面特定元素，自动暂停并告警
- **新鲜度过滤**：只处理 N 天内的评论（可配置）
