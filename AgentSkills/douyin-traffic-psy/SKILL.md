---
name: douyin-traffic-psy-v3
description: "抖音智能引流助手 V3 — 标准化交付版。V2 零快照架构 + AI 自动初始化引导 + 行业预设模板 + 一键环境诊断 + 配置导入导出。开箱即用，适合批量部署。"
description_zh: "抖音引流V3：标准化交付、零快照、行业模板、一键诊断"
description_en: "Douyin Traffic V3 - Standardized delivery, zero-snapshot, industry templates, one-click diagnostics"
version: 2.3.0
---

# psy-douyin-traffic — 抖音智能引流（V3 正式版）

> **这是当前唯一维护的版本。** 旧版 `抖音引流-psy`（V1）、`douyin-traffic-psy-v2` 已弃用，请勿在新账号中使用。
>
> **核心理念（继承 V2）**：能不取快照就别取快照。所有页面交互通过 `evaluate_script` 精准提取数据 + CSS 选择器直接定位元素。
>
> **V3 新增**：AI 自动初始化引导 + 行业预设模板 + 一键环境诊断 + 配置导入导出。**开箱即用，适合批量交付给多用户。**

---

## V2 → V3 核心改动

| 维度 | V2 | V3 |
|------|----|----|
| 首次使用 | 手动编辑 config.json | AI 对话式引导配置 |
| 环境检测 | 文字说明 | `setup_wizard.py` 一键诊断 |
| 话题配置 | 手动写 JSON | 7 大行业预设模板，AI 智能生成 |
| 跨机器部署 | 手动复制文件 | `export` / `import-config` 命令 |
| 故障排查 | 手动看故障表 | 自动诊断 + 状态检查 |
| 配置管理 | 基础读写 | 完整 CRUD + 导入导出 + 行业模板 |

---

## 🚀 标准化交付引导（AI 必读 — 首次运行时执行）

> **触发条件**：当检测到以下任一情况时，AI **必须**自动进入初始化引导流程：
> 1. 用户首次使用此技能（config.json 中 `_initialized` 为 `false` 或 `topics` 为空）
> 2. 用户明确表示「刚安装」「新用户」「第一次用」「帮我设置」
> 3. 用户说「设置抖音引流」「配置引流」

### Phase 1: 环境自检（自动，无需用户操作）

AI 应按以下顺序逐项检测，每项显示 ✅ 或 ❌：

| # | 检测项 | 方法 | 通过条件 | 失败处理 |
|---|--------|------|----------|----------|
| 1 | Chrome 版本 | `evaluate_script({ function: "return navigator.userAgent" })` 提取版本号 | Chrome ≥ 144 | 提示更新 Chrome |
| 2 | MCP 配置 | 读取 `~/.workbuddy/mcp.json` | 存在 chrome-devtools + `--autoConnect` | 提供配置内容，写入 |
| 3 | 浏览器连接 | `evaluate_script({ function: "return document.title" })` | 能成功返回值 | 提示开启远程调试 |
| 4 | 抖音登录 | `evaluate_script` 调用 `checkLoginStatus()` | `isLoggedIn: true` | 提示登录抖音 |
| 5 | Node.js | `execute_command` 运行 `node --version` | 版本 ≥ 18 | 提示安装 Node.js |
| 6 | 技能配置 | `execute_command` 运行 `python config_manager.py check` | `_initialized: true` + 有话题 | 进入 Phase 2 |

> **快捷方式**：AI 可以先运行 `execute_command` 执行 `python {技能目录}/scripts/setup_wizard.py check`，一次性获取完整环境诊断报告。

**如果 MCP 未配置，AI 应提供以下配置并写入 `~/.workbuddy/mcp.json`**：

```json
{
  "mcpServers": {
    "chrome-devtools": {
      "command": "npx",
      "args": ["@anthropic-ai/mcp-server-chrome-devtools@latest", "--autoConnect"]
    }
  }
}
```

**Phase 1 通过后**，进入 Phase 2。

---

### Phase 2: 业务配置（对话式引导）

AI 通过对话完成所有配置，**用户不需要手动编辑任何文件**。

#### Step 2.1: 询问引流领域

```
AI: 请问你要引流的领域是什么？
    常见选项：旅游 / 教育 / 电商 / 本地生活 / 知识付费 / 健身 / 美妆 / 其他
    
用户: 旅游

AI: 好的，旅游领域。你的目标城市或具体方向是什么？
    例如：三亚、云南、成都、日本旅游...
    
用户: 云南
```

#### Step 2.2: AI 生成预设配置

AI 根据 V3 的行业预设模板库，自动生成配置：

**行业预设模板库**（内置在 `config_manager.py` 的 `INDUSTRY_TEMPLATES` 中）：

| 领域 | 搜索关键词 | 匹配关键词示例 | 回复模板示例 |
|------|-----------|--------------|-------------|
| 旅游 | {城市}旅游攻略 2026 | 求攻略, 路线, 怎么去, 避坑 | 刚从XX回来，整理了攻略，私信我~ |
| 教育 | {科目}学习方法 | 怎么学, 提分, 零基础, 资料 | 整理了一套学习资料，私信免费分享 |
| 电商 | {产品}推荐 | 怎么选, 哪个好, 性价比 | 用了几个月，亲测好用，私信告诉你 |
| 健身 | 减肥/增肌 | 怎么减, 求计划, 饮食, 瘦腿 | 3个月减了XX斤，方法很简单，私信分享 |
| 美妆 | {产品}测评 | 怎么用, 避坑, 适合, 平价 | 用了一段时间，真实感受，私信分享 |
| 本地生活 | {城市}美食/探店 | 好吃的, 求推荐, 打卡, 探店 | 整理了一份美食地图，私信发你 |
| 知识付费 | {主题}入门 | 怎么入门, 求资料, 课程, 副业 | 整理了入门资料包，私信免费分享 |
| 通用 | — | 求推荐, 怎么选, 求攻略 | 整理了详细资料，需要的私信我~ |

> AI 应根据用户的具体领域**智能生成**匹配的关键词和模板。如果用户说的领域不在上表中，AI 应使用通用模板并根据领域特点自定义。

#### Step 2.3: 展示配置并确认

```
AI: 我帮你生成了一套云南旅游的预设配置：
    
    📋 话题：云南旅游引流
    🔍 搜索关键词：旅游 云南
    🎯 匹配关键词：求攻略, 路线, 怎么去, 求推荐, 几月去好, 避坑, 自驾, 行程安排, 第一次去, 怎么玩
    💬 回复模板（4个）：
       1. "刚从云南回来，整理了一份超详细攻略，需要的可以私信我~"
       2. "推荐几个云南必去的地方，篇幅有限私信发你完整版"
       3. "云南吃喝玩乐全攻略我有整理，私信免费分享给你"
       4. "避坑指南+省钱攻略都有，私信发你~"
    
    你可以修改任何内容，或者直接确认使用这套配置。
    
用户: 可以，用这套
    
AI: ✅ 配置已保存！还要添加其他话题吗？（最多可配 5 个话题）
```

> **技术实现**：AI 调用 `execute_command` 运行 `python {技能目录}/scripts/config_manager.py export-session` 查看当前配置状态，然后通过对话获取用户输入，最后直接写入 `config.json`。

---

### Phase 3: 确认运行参数

```
AI: 运行参数确认：
    📊 日回复上限：30 条
    ⏰ 活跃时段：9:00 - 23:00
    ⏱️ 回复间隔：45-120 秒随机
    🎬 观看时长：15-45 秒随机
    🔄 运行模式：半自动（每步需确认）
    
    以上参数是否需要调整？（一般不需要改动）
```

---

### Phase 4: 试运行

```
AI: 环境检测全部通过 ✅，配置已就绪！
    
    建议先做一次试运行：处理 1 个视频，确认流程正常。
    试运行开始？
    
用户: 开始
    
（AI 执行完整流程：搜索 → 排序 → 选 1 个视频 → 扫描评论 → 匹配 → 回复）
    
AI: 🎉 试运行完成！
    ✅ 扫描评论 45 条
    ✅ 匹配关键词 3 条
    ✅ 成功回复 1 条
    
    数据已保存到 data/session_xxx.json
    
    现在可以正式开始批量运行了。发送「开始」即可。
```

---

## 依赖技能

1. Chrome ≥ 144，已在 `chrome://inspect/#remote-debugging` 开启远程调试
2. MCP 配置已写入 `~/.workbuddy/mcp.json`（chrome-devtools server，`--autoConnect` 模式）
3. Chrome 已登录抖音账号

---

## 配置文件

V3 的 config.json 新增了初始化状态字段：

```json
{
  "_version": "3.0",
  "_initialized": false,
  "topics": [
    {
      "name": "话题名称",
      "search_keyword": "搜索关键词",
      "enabled": true,
      "keywords": ["关键词1", "关键词2"],
      "reply_templates": ["模板1", "模板2", "模板3"],
      "max_videos": 3,
      "max_replies_per_video": 1,
      "max_daily_replies": 15
    }
  ],
  "global_settings": {
    "daily_reply_limit": 30,
    "reply_interval_min_seconds": 45,
    "reply_interval_max_seconds": 120,
    "video_watch_min_seconds": 15,
    "video_watch_max_seconds": 45,
    "action_delay_min_seconds": 3,
    "action_delay_max_seconds": 8,
    "active_hours_start": 9,
    "active_hours_end": 23,
    "comment_scroll_rounds": 3,
    "auto_mode": false
  },
  "data_dir": "data",
  "log_level": "info"
}
```

---

## JS 工具脚本（scripts/douyin_tools.js）

基于 V2 工具集，V3 新增了 2 个函数：

| # | 函数 | 用途 | 返回值 |
|---|------|------|--------|
| 1 | `searchVideo(keyword)` | 搜索视频 | `{ success, keyword }` |
| 2 | `sortByHot()` | 按热度排序 | `{ success, sortBy }` |
| 3 | `extractVideoList(maxCount)` | 提取视频列表（v2.3 多策略容错） | `{ count, videos: [{title, author, likes, videoId, url}], _debug }` |
| **3.5** | **`extractVideoIds(maxCount)`** | **V3 新增：从搜索结果提取 videoId** | `{ count, videoIds: [] }` |
| 4 | `parseVideoUrl(href)` | 解析视频 URL | `{ videoId, fullUrl }` |
| 5 | `extractComments()` | 提取评论（含 time 时间） | `{ total, comments: [{author, text, likes, time, ...}] }` |
| 6 | `scrollCommentArea()` | 滚动评论区（v2.3 WheelEvent） | `{ scrollTop, canScrollMore, method }` |
| 7 | `findAndClickReply(text)` | 点击回复按钮（只点击不等待） | `{ success, message }` |
| 7.5 | `waitForReplyInput()` | 检测输入框状态 | `{ found, focused, visible }` |
| 8 | `typeReply(text)` | ⚠️ 输入回复文本（**推荐用 MCP `type_text`**） | `{ success, currentText }` |
| 9 | `submitReply()` | ⚠️ 提交回复（**推荐用 MCP `press_key "Enter"`**） | `{ success, message }` |
| **9.1** | **`checkReplySubmitted()`** | **v2.1 新增：检查回复是否已提交** | `{ submitted, message }` |
| 10 | `extractVideoInfo()` | 提取视频信息（v2.3 h1 兜底） | `{ title, author, likes, comments, publishTime, videoId, _selectors }` |
| 11 | `checkCaptcha()` | 检测验证码 | `{ safe, hasCaptcha, hasSlider, hasBlock }` |
| **11.5** | **`checkLoginStatus()`** | **V3 新增：检测登录状态** | `{ isLoggedIn, hasAvatar }` |
| **13** | **`extractVideoPublishTime()`** | **v2.2 新增：提取视频发布时间** | `{ success, raw }` |
| **14** | **`parseTimeAgo(timeStr)`** | **v2.2 新增：中文时间→小时数** | `{ hours, days, text }` |
| **15** | **`diagnosePage()`** | **v2.3 新增：页面结构诊断（选择器失效时调用）** | `{ pageType, videoLinks, commentArea, searchContainerCandidates, h1, ... }` |
| **16** | **`probeSelector(selectors)`** | **v2.3 新增：批量探测选择器是否有效** | `{ "selector": { count, firstText, firstClass } }` |
| 12 | `batchScan(keywords, rounds)` | 一站式批量扫描 | `{ totalScanned, matches }` |

---

## 工作流程（SOP）

### 状态机

```
[初始化] → [搜索话题] → [排序] → [提取视频列表] → [选择视频]
   ↑                                                    ↓
[结束/切换] ← [返回] ← [记录结果] ← [回复评论] ← [扫描匹配评论]
                                        ↑
                                  [导航视频详情]
```

### 详细步骤

#### Step 1: 初始化检查

1. 读取 `config.json`
2. 检查 `_initialized` 状态，如为 `false` 则进入「标准化交付引导」流程
3. 检查日限额、活跃时段
4. 通过 `evaluate_script` 检查浏览器连接
5. **[暂停]** 展示配置，等待确认

#### Step 2: 搜索话题

> ⚠️ **v2.2.0 发现**：搜索 URL 必须加 `?type=video` 参数，否则搜索结果页不包含视频链接（videoId 为 null）。

1. `navigate_page` → `https://www.douyin.com/search/{keyword}?type=video`
2. `wait_for` → 等待搜索结果出现
3. **0 快照**

#### Step 3: 按热度排序

1. `evaluate_script` → 调用 `sortByHot()`
2. `wait_for` → 短暂延迟
3. **0 快照**

#### Step 4: 提取视频列表 + 智能筛选

> ⚠️ **v2.2.0 更新**：视频选择需同时考虑**热度**、**评论新鲜度**和**防重复**。

1. `evaluate_script` → 调用 `extractVideoList(maxCount)`（获取 5-10 条）
2. 如果 `videoId` 为 null，用 `extractVideoIds()` 补充提取
3. **防重复过滤**：通过 `config_manager.py` 的 `get_replied_video_ids()` 获取已回复视频列表，过滤掉已处理过的视频
4. AI 在本地做智能筛选（不消耗额外 token），选择标准：
   - **热度适中**：不要选顶流（竞争太激烈），也不要选太冷门的
   - **评论新鲜度**：优先选有近期评论的视频（评论时间 < 1 周的才有引流效果）
   - **匹配概率**：看视频标题/描述是否与目标关键词相关
5. **0 快照**

#### Step 5: 导航视频详情 + 新鲜度检测

> ⚠️ 抖音搜索页是纯 SPA 架构，视频卡片没有链接。进入视频只能通过 `navigate_page`。

1. 从 Step 4 筛选结果中选择目标视频
2. `navigate_page` → `https://www.douyin.com/video/{videoId}`
3. `wait_for` → 等评论区加载
4. `evaluate_script` → 调用 `extractVideoInfo()` 获取视频详情（含 `publishTime`）
5. 新鲜度判断：调用 `parseTimeAgo(publishTime)`，如果视频发布超过 1 个月，跳过
6. 随机等待 15-45 秒模拟观看
7. **0 快照**

#### Step 6: 扫描匹配评论（含新鲜度过滤）

1. `evaluate_script` → 调用 `extractComments()` 获取评论（每条含 `time` 字段）
2. 需要加载更多：循环滚动评论区 + `extractComments()`，每轮去重
   - ⚠️ **v2.2.0 发现**：抖音评论区使用虚拟滚动，`scrollTop` 赋值无效。必须用 `WheelEvent` 模拟鼠标滚轮触发懒加载：
   ```javascript
   container.dispatchEvent(new WheelEvent('wheel', {
     bubbles: true, cancelable: true,
     clientX: centerX, clientY: centerY,
     deltaY: 800, wheelDelta: -800
   }));
   ```
   - `centerX/centerY` 取 `.comment-mainContent` 的矩形中心坐标
3. 或使用一站式 `batchScan(keywords, rounds)`
4. AI 在本地做**双重过滤**（不消耗额外 token）：
   - **关键词匹配**：评论文本是否包含目标关键词
   - **新鲜度过滤**：调用 `parseTimeAgo(comment.time)`，**超过 1 周（168小时）的评论跳过**，引流效果太低
5. **防重复过滤**：检查匹配到的评论是否已在 `replied.json` 中（同一视频+同一评论不重复回复）
6. **0 快照**

#### Step 7: 回复评论

> ⚠️ **CRITICAL（v2.1.0 更新）**：回复提交流程必须使用 MCP 原生工具！不要用 `evaluate_script` 输入文本或模拟键盘事件，会导致 React Draft.js 组件崩溃、评论区 DOM 卸载。

```
第1步 evaluate_script: findAndClickReply('评论文本')     → 点击回复按钮
第2步 MCP type_text:   type_text({ text: '回复内容' })     → 输入文本（不用 evaluate_script！）
第3步 MCP press_key:    press_key({ key: 'Enter' })         → 提交（Enter 键，不是 Ctrl+Enter！）
第4步 evaluate_script: checkReplySubmitted()                → 验证提交状态
```

**为什么不能用 evaluate_script 输入文本？**
- 抖音评论输入框是 React Draft.js 组件，`execCommand('insertText')` 会导致 React 内部状态不一致
- 轻则评论区 DOM 卸载需要 reload 恢复，重则回复内容丢失
- MCP 的 `type_text` 工具模拟真实键盘输入，兼容 Draft.js

**提交快捷键是 Enter（不是 Ctrl+Enter）**
- 抖音 PC 端评论提交：输入框聚焦时按 Enter
- Ctrl+Enter 不会触发提交
- 发送按钮（红色 SVG 图标 `.WFB7wUOX`）在输入框聚焦时 `display: none`，无法点击

#### Step 8: 记录结果 + 防重复标记

> ⚠️ **v2.2.0 更新**：每次回复成功后，**必须**同时写入 session 文件和防重复记录。

**每条回复成功后立即执行：**

1. **写入防重复记录**（防止下次重复回复同一评论）：
   ```
   evaluate_script: add_replied_record(
     video_id, video_title, video_author,
     comment_author, comment_text,
     reply_content, search_keyword, topic_name
   )
   ```
   → 实际通过 `execute_command` 调用 `config_manager.py`，或由 AI 直接写入 `data/replied.json`

2. **一个视频处理完后，汇总写入 session 文件**：
   - AI 将执行数据通过 `execute_command` 调用 `config_manager.py` 保存 session
   - 或直接写入 `data/session_{YYYYMMDD}_{HHmmss}.json`

3. **每次运行结束（所有视频处理完后）**，执行 `python config_manager.py stats` 展示今日统计

**session 数据结构**（供 AI 参考）：
```json
{
  "stats": { "videos_visited": 3, "comments_scanned": 156, "comments_matched": 12, "replies_sent": 3 },
  "actions": [
    { "step": "reply_sent", "video_id": "...", "video_title": "...", "video_author": "...",
      "comment_author": "...", "comment_text": "...", "reply_content": "...",
      "search_keyword": "...", "topic_name": "..." }
  ]
}
```

4. 判断是否继续下一个视频或话题
5. 结束或回到 Step 2

---

## 风控安全策略

| 策略 | 参数 | 说明 |
|------|------|------|
| 操作间隔 | 3-8 秒随机 | 每个页面操作间等待 |
| 评论间隔 | 45-120 秒随机 | 两次回复评论间等待 |
| 日回复上限 | ≤30 条 | 防止异常高频回复 |
| 单视频回复 | ≤1 条 | 避免同一视频多次回复 |
| 活跃时段 | 9:00-23:00 | 非活跃时段不操作 |
| 视频观看 | 15-45 秒 | 模拟真人观看时长 |
| 模板轮换 | 不连续使用同一模板 >2 次 | 防止内容重复被识别 |
| 验证码检测 | 每步自动检测 | 检测到立即暂停 |
| **评论新鲜度** | **>1周（168小时）跳过** | **v2.2 新增：老评论引流效果差** |
| **防重复回复** | **已回复视频/评论自动跳过** | **v2.2 新增：replied.json 去重** |
| **视频新鲜度** | **发布 >1月跳过** | **v2.2 新增：老视频评论区活跃度低** |

---

## 交互指令

半自动模式下（`auto_mode: false`），每步暂停等待确认：

| 指令 | 缩写 | 说明 |
|------|------|------|
| `继续` | `y` / 回车 | 执行下一步 |
| `跳过` | `s` | 跳过当前步骤 |
| `修改` | `m` | 修改配置后继续 |
| `停止` | `q` | 结束当前话题 |
| `自动` | `a` | 切换为全自动模式 |
| `状态` | `st` | 查看当前统计 |
| `帮助` | `h` | 显示指令帮助 |

---

## 故障排查

| 问题 | 排查方式 | 解决方案 |
|------|----------|----------|
| evaluate_script 返回 null | `take_snapshot` 兜底查看页面 | 页面可能未加载完成，增加 `wait_for` |
| 找不到回复按钮 | `take_snapshot` 查看评论区结构 | 抖音 DOM 可能更新，更新选择器 |
| **typeReply 报 "input not found"** | 调用 `waitForReplyInput()` 检查 | React 未渲染完，重试 `typeReply()` |
| **typeReply 返回空文本** | 检查 `currentText` 字段 | 输入框可能失焦 |
| **评论区 DOM 消失** | `navigate_page` reload 刷新 | 滚动或播放可能导致评论区卸载 |
| **搜索结果无法进入视频** | 用 `navigate_page` 直接到 `/video/{id}` | SPA 无 href 链接 |
| 触发验证码 | `checkCaptcha()` 自动检测 | 立即停止，等人工处理 |
| **typeReply 后评论区 DOM 消失** | **不要用 evaluate_script 的 typeReply**，改用 MCP `type_text` 工具 | React Draft.js 组件崩溃 |
| **submitReply 找不到发送按钮** | **不要用 evaluate_script 提交**，改用 MCP `press_key "Enter"` | 输入框聚焦时发送按钮被隐藏 |
| **Ctrl+Enter 无法提交回复** | **使用 Enter 键（不带 Ctrl）** | 抖音 PC 端评论用 Enter 提交 |
| 回复发送失败 | 检查 `submitReply()` 返回值 | 可能输入框未聚焦，重试 |
| **环境问题** | `python setup_wizard.py check` | 一键诊断所有环境项 |
| **浏览器连接失败/超时** | 按「浏览器连接排错指南」逐步排查 | 最常见原因：远程调试未开启或 MCP 未重启 |
| **所有视频都已回复过** | `python config_manager.py replied` 查看，或 `clear-replied` 清除 | replied.json 记录了30天内的已回复视频 |
| **评论时间提取为空** | 抖音 DOM 可能更新了时间选择器 | 仍可正常回复，但无法做新鲜度过滤 |
| **搜索结果无 videoId** | **搜索 URL 加 `?type=video` 参数** | 不加参数时 SPA 搜索结果不包含视频链接 |
| **评论区滚动无效** | **v2.3 已修复**：改用 WheelEvent | `scrollCommentArea()` 已自动使用 WheelEvent |
| **extractVideoList 返回 0 条** | 调用 `diagnosePage()` 查看页面结构 | 见下方「选择器失效 SOP」 |

---

## 🔧 选择器失效 SOP（v2.3.0 新增 — AI 必读）

> **触发条件**：当 `extractVideoList().count === 0`、`extractComments().total === 0`、或 `extractVideoInfo().title === "unknown"` 时，**必须**按此流程排查。

### 为什么选择器会失效？

抖音前端使用 CSS Modules（class 名会哈希化），例如 `.AMqhOzPC` 是哈希后的 class，每次版本更新都可能变化。
`data-e2e` 属性相对稳定但也可能被移除。**v2.3.0 已将核心函数改为多策略容错，但如果还是失败，按以下流程处理：**

### 排查流程

#### Step 1：调用 diagnosePage() 获取页面诊断报告

```javascript
// evaluate_script 调用
diagnosePage()
```

查看返回值：
- `pageType`：确认是否在正确页面（search / video / home）
- `videoLinks`：是否有 `a[href*="/video/"]` 链接（如果 > 0，extractVideoList 策略1应该能工作）
- `searchContainerCandidates`：哪些 class 包含 "search"/"result" 等关键词（用于找新容器选择器）
- `commentArea`：哪个评论区选择器有效

#### Step 2：用 probeSelector() 测试候选选择器

```javascript
// 根据 diagnosePage() 的结果，测试具体选择器
probeSelector([
  '[class*="search"]',
  '[class*="videoCard"]',
  '[class*="searchCard"]',
  'a[href*="/video/"]',
  '.comment-mainContent'
])
```

#### Step 3：如果以上都无效，截图兜底

如果 `diagnosePage()` 也无法定位元素，说明页面结构发生了根本性变化：

1. **调用 `take_snapshot`** 截取当前页面快照
2. AI 分析快照，找到新的元素结构
3. 将新选择器更新到 `douyin_tools.js` 对应函数中

#### Step 4：更新选择器

找到有效选择器后，更新 `scripts/douyin_tools.js` 中对应函数，并在注释中标注日期：

```javascript
// v2.3.x 更新（YYYY-MM-DD 发现）：原 xxx 选择器失效，改为 yyy
```

### 常见哈希 class 替代策略

| 失效选择器 | 稳定替代策略 |
|-----------|------------|
| `.AMqhOzPC` | `a[href*="/video/"]` + 向上找卡片容器 |
| `.pMq55q1M`（点赞数） | `[class*="like"]`、`[class*="digg"]` |
| `.FnM1bbIQ`（时长） | `[class*="duration"]`、`[class*="time"]` |
| `[data-e2e="video-title"]` | `h1`、`[class*="title"]`、`[class*="desc"]` |
| `[data-e2e="comment-item"]` | `.comment-mainContent > div > div`、`[class*="commentItem"]` |
| `[data-e2e="video-author-name"]` | `a[href*="/@"] span`、`[class*="nickName"]` |

---

## 🔧 浏览器连接排错指南（AI 必读）

> **触发条件**：当 Phase 1 环境自检中 `list_pages` 或 `evaluate_script` 连接失败/超时时，AI **必须**按此指南逐步排查。

### 连接架构说明

```
WorkBuddy (AI) → MCP Server (npx chrome-devtools-mcp) → Chrome (CDP 协议)
```

- `--autoConnect` 模式：MCP 自动发现已开启远程调试的 Chrome，**无需指定端口**
- Chrome 136+ 的安全策略：`/json/version`、`/json/list` 等 HTTP API 返回 **404**，但 CDP WebSocket 仍可用
- MCP 的 `--autoConnect` 走的是 CDP 发现机制，**不依赖** `/json/version` HTTP 接口

### 排错流程（按顺序执行）

#### ❌ 现象：`list_pages` 超时或返回错误

**Step 1: 确认 Chrome 是否在运行**
```powershell
tasklist | Select-String "chrome"
```
- 无结果 → 启动 Chrome
- 有结果 → 继续 Step 2

**Step 2: 确认远程调试是否已开启**

要求用户确认：
- Chrome 地址栏输入 `chrome://inspect/#remote-debugging`
- 页面是否显示 **"Allow remote debugging for this browser instance"** 且状态为开启
- 页面是否显示 **"Server running at: 127.0.0.1:xxxxx"**

如果没开启 → 点击开启，**不要关掉这个页面**，继续 Step 3

> ⚠️ **关键**：`chrome://inspect/#remote-debugging` 页面**必须保持打开**，关掉后调试服务会停止。

**Step 3: 确认 MCP 配置**

读取 `~/.workbuddy/mcp.json`，确认配置正确：

```json
{
  "mcpServers": {
    "chrome-devtools": {
      "command": "npx",
      "args": ["-y", "chrome-devtools-mcp@latest", "--autoConnect"],
      "type": "stdio",
      "disabled": false
    }
  }
}
```

检查要点：
- `args` 中必须包含 `--autoConnect`（不要用 `--port=xxx`，autoConnect 会自动发现）
- `disabled` 必须为 `false`
- 包名是 `chrome-devtools-mcp@latest`

**Step 4: 确认 Chrome 版本 ≥ 144**

`--autoConnect` 模式要求 Chrome M144+。在 Chrome 地址栏输入 `chrome://version` 查看版本号。

**Step 5: 重载 WorkBuddy 让 MCP 重启**

修改 `mcp.json` 后，需要让 MCP 服务重启才能生效：
- 方式 1：`Ctrl+Shift+R` 重载 WorkBuddy 窗口
- 方式 2：关闭并重新打开 WorkBuddy

**Step 6: Chrome 权限弹窗**

`--autoConnect` 首次连接时，Chrome 会**弹出权限确认对话框**（"是否允许远程调试连接"）。
- ⚠️ **用户必须点击"允许"**，否则连接会被拒绝
- 提醒用户注意观察 Chrome 窗口是否有弹窗

**Step 7: 验证连接**

重载后让 AI 执行 `list_pages`，如果返回页面列表则连接成功。

### 常见问题速查表

| 现象 | 原因 | 解决 |
|------|------|------|
| `list_pages` 超时 | Chrome 未开 / 远程调试未开 | Step 1-2 |
| 修改 mcp.json 后仍连不上 | MCP 未重启 | Step 5: 重载 WorkBuddy |
| `/json/version` 返回 404 | Chrome 136+ 正常行为 | 不影响，autoConnect 不走这个接口 |
| 连接后立刻断开 | Chrome 权限弹窗未点允许 | Step 6: 点"允许" |
| 端口从 57863 变成其他数字 | 每次开启远程调试端口随机 | 用 `--autoConnect` 自动发现，不用指定端口 |
| Chrome 重启后连不上 | 远程调试需重新开启 | 重新去 `chrome://inspect/#remote-debugging` 开启 |
| `npx` 命令找不到 | Node.js 未安装或不在 PATH | 运行 `setup_wizard.py check` 诊断 |

### 不推荐的方案

- ❌ **不要用 `--port=xxx` 直连端口**：Chrome 136+ 的 HTTP API 返回 404，直连可能失败
- ❌ **不要用 `--remote-debugging-port` 启动 Chrome**：这种方式在 Chrome 136+ 同样 404
- ✅ **正确方案**：`chrome://inspect/#remote-debugging` 开启 + `--autoConnect` 自动发现

### 快速修复口诀

```
1. Chrome 打开着？ ✅
2. chrome://inspect/#remote-debugging 开着？ ✅
3. mcp.json 有 --autoConnect？ ✅
4. WorkBuddy 重载了？ ✅
5. Chrome 弹窗点允许了？ ✅
→ 还不行？运行 setup_wizard.py check
```

---

## 数据记录

session 文件存储在 `data/` 目录：

**文件名**：`session_{YYYYMMDD}_{HHmmss}.json`

**数据结构**：
```json
{
  "session_id": "20260403_110000",
  "version": "3.0",
  "start_time": "2026-04-03T11:00:00",
  "end_time": "2026-04-03T11:15:00",
  "topics_processed": ["云南旅游引流"],
  "stats": {
    "videos_visited": 3,
    "comments_scanned": 156,
    "comments_matched": 12,
    "replies_sent": 3,
    "captcha_detected": 0,
    "snapshots_used": 0
  },
  "actions": [ ... ]
}
```

---

## 文件结构

```
douyin-traffic-psy-v3/
├── SKILL.md                    # 本文档
├── _skillhub_meta.json         # 技能元数据
├── config.json                 # 用户配置（含初始化状态）
├── scripts/
│   ├── douyin_tools.js         # V3 核心工具集（evaluate_script 注入）
│   ├── config_manager.py       # V3 增强配置管理器（行业模板+导入导出）
│   └── setup_wizard.py         # V3 新增：一键环境诊断
└── data/                       # 数据记录目录
    ├── session_*.json          # session 记录（每次运行）
    ├── replied.json            # v2.2 新增：已回复去重记录（30天自动清理）
    └── config_export.json      # 导出的配置文件（可选）
```

---

## 配置管理命令参考

| 命令 | 说明 |
|------|------|
| `python config_manager.py check` | 检查初始化状态 |
| `python config_manager.py show` | 显示当前配置 |
| `python config_manager.py stats` | 显示今日统计 |
| `python config_manager.py history [days]` | **v2.2 新增：显示历史记录**（默认7天，带搜索关键字/视频/评论详情） |
| `python config_manager.py replied` | **v2.2 新增：显示最近回复记录**（最新20条） |
| `python config_manager.py is-replied <video_id>` | **v2.2 新增：检查视频是否已回复** |
| `python config_manager.py clear-replied` | **v2.2 新增：清除所有已回复记录** |
| `python config_manager.py templates` | 显示可用行业模板 |
| `python config_manager.py export` | 导出配置为 JSON |
| `python config_manager.py import-config <文件>` | 导入配置 |
| `python config_manager.py init` | 重置为默认配置 |
| `python setup_wizard.py` | 完整环境诊断 |
| `python setup_wizard.py check` | 仅环境检测 |
| `python setup_wizard.py mcp` | 显示 MCP 配置说明 |
