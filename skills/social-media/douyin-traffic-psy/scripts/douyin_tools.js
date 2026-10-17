/**
 * 抖音引流-psy V3 — 零快照工具集 v2.4.0
 *
 * 基于 V2 工具集，增加：
 *   - extractVideoId() 从搜索结果提取 videoId（解决 SPA 无链接问题）
 *   - enhancedCheckCaptcha() 增强验证码检测
 *
 * v2.4.0 更新（2026-06-18 实测验证）：
 *   - extractComments() 子选择器大修：nickName/authorName/name 全部失效，改用 innerText 行解析兜底
 *   - checkCaptcha() 修复 slider 误报：排除视频进度条，精确匹配 captcha slider
 *   - extractVideoInfo() 修复 h1/h2 误匹配导航栏：增加视频容器 scoping + 排除 <a> 标签
 *
 * v2.1.0 更新（2026-04-04 实测验证）：
 *   - submitReply() 改用 Enter 键提交（不是 Ctrl+Enter）
 *   - typeReply() 的 execCommand 方式会导致 React DOM 崩溃，建议用 MCP type_text 代替
 *   - 新增 submitReplyByEnter() 专用 Enter 提交函数
 *   - 评论区 DOM 结构：.comment-mainContent > div > div.UuCzPLbi[data-e2e="comment-item"]
 *   - 发送按钮是红色 SVG 图标（.WFB7wUOX），但输入框聚焦时 display:none
 *   - 修复 extractComments() 选择器
 *
 * v2.2.0 更新（2026-04-04）：
 *   - extractComments() 新增 time 字段（评论发布时间，如"3小时前"、"2天前"）
 *   - 新增 extractVideoPublishTime() 提取视频发布时间
 *   - 新增 parseTimeAgo() 将中文时间转为小时数（用于新鲜度判断）
 *
 * v2.3.0 更新（2026-04-05 实测验证 — 选择器大修）：
 *   - extractVideoList() 彻底重写：.AMqhOzPC 失效，改用多策略容错选择器
 *   - scrollCommentArea() 改用 WheelEvent 驱动懒加载（scrollTop 赋值无效）
 *   - extractVideoInfo() 新增 h1 兜底，title/author/likes 选择器全面加固
 *   - 新增 diagnosePage() 诊断函数：页面结构截面快照，用于选择器失效时排查
 *   - 新增 probeSelector() 批量探测选择器是否存在（辅助选择器调试）
 *
 * 设计原则同 V2：
 *   1. 每个函数同步执行，返回精简 JSON
 *   2. 不依赖 take_snapshot，纯 DOM 操作
 *   3. 通过 evaluate_script 注入调用
 *   4. findAndClickReply 和 typeReply 必须分成两次 evaluate_script 调用
 *   5. 【重要】提交回复用 press_key Enter（不是 evaluate_script），避免 React 崩溃
 *
 * 选择器容错策略（v2.3.0）：
 *   抖音 class 名经常哈希化（如 .AMqhOzPC 会失效），优先级：
 *   1. a[href*="/video/"] — 链接最稳定
 *   2. [class*="关键词"] — 部分匹配比精确匹配稳定
 *   3. data-e2e 属性 — 可能被移除，作为备选
 *   4. innerText / TextWalker 扫描 — 最后兜底
 */

// ─────────────────────────────────────────────
// [1] 搜索视频
// ─────────────────────────────────────────────
const searchVideo = (keyword) => {
  const input = document.querySelector('[data-e2e="searchbar-input"]')
    || document.querySelector('input[placeholder*="搜索"]')
    || document.querySelector('input[type="search"]');

  if (!input) return { success: false, message: 'search input not found' };

  input.focus();
  input.value = keyword;

  const nativeInputValueSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
  nativeInputValueSetter.call(input, keyword);
  input.dispatchEvent(new Event('input', { bubbles: true }));
  input.dispatchEvent(new Event('change', { bubbles: true }));

  const searchBtn = document.querySelector('[data-e2e="searchbar-button"]')
    || document.querySelector('button[data-e2e*="search"]')
    || document.querySelector('[class*="searchBtn"]');

  if (searchBtn) {
    searchBtn.click();
  } else {
    input.dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter', keyCode: 13, bubbles: true }));
  }

  return { success: true, keyword: keyword };
};

// ─────────────────────────────────────────────
// [2] 按热度排序
// ─────────────────────────────────────────────
const sortByHot = () => {
  const tabs = document.querySelectorAll('[class*="tab"] span, [class*="tag"] span, [data-e2e*="sort"] span, a span');

  for (const tab of tabs) {
    const text = tab.innerText.trim();
    if (text === '最热' || text === '最多点赞' || text === '综合') {
      tab.click();
      return { success: true, sortBy: text };
    }
  }

  const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
  let node;
  while ((node = walker.nextNode())) {
    const t = node.textContent.trim();
    if (t === '最热' || t === '最多点赞') {
      const clickable = node.parentElement;
      if (clickable) {
        clickable.click();
        return { success: true, sortBy: t };
      }
    }
  }

  return { success: false, message: 'hot sort tab not found' };
};

// ─────────────────────────────────────────────
// [3] 提取视频列表（v2.3.0 重写 — 多策略容错）
//
// ⚠️ v2.3.0 关键修复：
//   - .AMqhOzPC 已失效（哈希化 class，抖音随时会改）
//   - 改用多策略容错：优先找视频链接，其次找搜索结果容器
//   - 当 URL 包含 ?type=video 时，视频卡片通常包含 a[href*="/video/"]
// ─────────────────────────────────────────────
const extractVideoList = (maxCount = 10) => {
  const results = [];
  const seen = new Set();

  // 策略1：优先从 a[href*="/video/"] 链接出发（最稳定）
  // 每个视频链接对应一张卡片，向上找最近的卡片容器
  const videoLinks = Array.from(document.querySelectorAll('a[href*="/video/"]'));

  for (const link of videoLinks) {
    if (results.length >= maxCount) break;

    const m = link.href.match(/video\/(\d+)/);
    if (!m) continue;
    const videoId = m[1];
    if (seen.has(videoId)) continue;
    seen.add(videoId);

    // 向上找卡片容器（最多5层）
    let card = link;
    for (let i = 0; i < 5; i++) {
      if (!card.parentElement) break;
      card = card.parentElement;
      // 卡片通常有一定高度且包含文本
      if (card.offsetHeight > 80 && (card.innerText || '').length > 20) break;
    }

    const cardText = card.innerText || '';
    const lines = cardText.split('\n').map(l => l.trim()).filter(Boolean);

    // 标题：最长的一行（排除 @ 开头、纯数字等噪声）
    const title = lines
      .filter(l => l.length > 5 && !l.startsWith('@') && !/^\d+[\w万亿]?$/.test(l))
      .sort((a, b) => b.length - a.length)[0] || lines[0] || '';

    const authorMatch = cardText.match(/@([\u4e00-\u9fa5\w.·_-]{1,30})/);
    const author = authorMatch ? authorMatch[1].trim() : '';

    // 点赞数：找数字+万/亿格式
    const likeMatch = cardText.match(/(\d+(?:\.\d+)?[万亿]?)\s*(?:赞|点赞|❤)/);
    const likes = likeMatch ? likeMatch[1] : '';

    results.push({
      title: title.substring(0, 80),
      author,
      likes,
      videoId,
      url: 'https://www.douyin.com/video/' + videoId
    });
  }

  // 策略2：如果策略1没找到（搜索结果无直链），尝试搜索结果容器
  if (results.length === 0) {
    // 抖音搜索结果容器 class 名经常变化，用多个候选
    const containerSelectors = [
      '[class*="search-result"]',
      '[class*="searchResult"]',
      '[class*="video-list"]',
      '[class*="videoList"]',
      '[class*="result-item"]',
      '[class*="resultItem"]'
    ];

    let items = [];
    for (const sel of containerSelectors) {
      items = Array.from(document.querySelectorAll(sel));
      if (items.length > 0) break;
    }

    for (const item of items.slice(0, maxCount)) {
      const linkEl = item.querySelector('a[href*="/video/"]');
      const videoId = linkEl ? (linkEl.href.match(/video\/(\d+)/) || [])[1] : null;
      if (!videoId || seen.has(videoId)) continue;
      seen.add(videoId);

      const text = item.innerText || '';
      const lines = text.split('\n').map(l => l.trim()).filter(Boolean);
      const title = lines.find(l => l.length > 5 && !l.startsWith('@')) || lines[0] || '';
      const authorMatch = text.match(/@([\u4e00-\u9fa5\w.·_-]{1,30})/);

      results.push({
        title: title.substring(0, 80),
        author: authorMatch ? authorMatch[1].trim() : '',
        likes: '',
        videoId,
        url: 'https://www.douyin.com/video/' + videoId
      });
    }
  }

  // 调试信息：帮助排查选择器失效
  const debugInfo = {
    strategy1_links: videoLinks.length,
    strategy2_used: results.length === 0 ? 'tried' : 'not_needed',
    url: window.location.href.substring(0, 80)
  };

  return { count: results.length, total: seen.size, videos: results, _debug: debugInfo };
};

// ─────────────────────────────────────────────
// [3.5] V3 新增：从搜索结果提取视频 ID
// 当 extractVideoList 无法获取 videoId 时，用此函数二次提取
// ─────────────────────────────────────────────
const extractVideoIds = (maxCount = 10) => {
  const ids = [];

  // 方法1：从搜索结果中找所有可能的 video URL
  const allLinks = document.querySelectorAll('a[href*="/video/"]');
  const seen = new Set();
  allLinks.forEach(a => {
    const m = a.href.match(/video\/(\d+)/);
    if (m && !seen.has(m[1]) && ids.length < maxCount) {
      seen.add(m[1]);
      ids.push(m[1]);
    }
  });

  // 方法2：从 data 属性中找
  if (ids.length === 0) {
    const rows = document.querySelectorAll('[class*="searchResult"], [class*="videoItem"], .AMqhOzPC');
    rows.forEach(row => {
      const html = row.innerHTML;
      const matches = html.matchAll(/video\/(\d+)/g);
      for (const m of matches) {
        if (!seen.has(m[1]) && ids.length < maxCount) {
          seen.add(m[1]);
          ids.push(m[1]);
        }
      }
    });
  }

  return { count: ids.length, videoIds: ids };
};

// ─────────────────────────────────────────────
// [4] 解析视频 URL
// ─────────────────────────────────────────────
const parseVideoUrl = (href) => {
  const match = (href || window.location.href).match(/video\/(\d+)/);
  return match
    ? { videoId: match[1], fullUrl: 'https://www.douyin.com/video/' + match[1] }
    : { videoId: null, fullUrl: null };
};

// ─────────────────────────────────────────────
// [5] 结构化提取评论（v2.4.0 重写 — innerText 行解析兜底）
//
// ⚠️ v2.4.0 关键修复（2026-06-18）：
//   - 抖音评论 DOM 中 nickName/authorName/name 等子选择器全部失效
//   - [class*="time"] / [class*="date"] 子选择器也失效
//   - 改用 innerText 行解析策略：分行提取作者、文本、时间、点赞、位置
//   - 评论 innerText 格式示例：
//       作者名
//       ...
//       评论文本内容
//       14小时前·上海
//       1          ← 点赞数
//       分享
//       回复
// ─────────────────────────────────────────────
const extractComments = () => {
  const comments = [];

  const commentItems = document.querySelectorAll(
    '[data-e2e="comment-item"], ' +
    '[class*="commentItem"], ' +
    '[class*="CommentItem"], ' +
    '.comment-mainContent > div > div'
  );

  if (commentItems.length === 0) {
    const container = document.querySelector('.comment-mainContent');
    if (container) {
      return {
        error: 'no comment items found via selectors',
        containerChildren: container.children.length,
        scrollTop: container.scrollTop,
        scrollHeight: container.scrollHeight
      };
    }
    return { error: 'comment area not found' };
  }

  commentItems.forEach(item => {
    // v2.4.0: 先尝试精确子选择器，全部失效时用 innerText 行解析
    const authorEl = item.querySelector('[data-e2e="comment-author-name"], [class*="authorName"], [class*="nickName"], [class*="name"]');
    const textEl = item.querySelector('[data-e2e="comment-text"], [class*="commentText"], [class*="content"], p');
    const timeEl = item.querySelector('[class*="time"], [class*="date"], [data-e2e="comment-time"], span[class*="Time"]');
    const likeEl = item.querySelector('[class*="like"], [class*="digg"], [data-e2e="comment-like"]');
    const expandEl = item.querySelector('[class*="expand"], [class*="subComment"]');

    let author = authorEl ? authorEl.innerText.trim() : '';
    let text = '';
    let time = '';
    let likes = '';

    if (author && textEl) {
      // 精确选择器有效 — 使用原逻辑
      text = textEl.innerText.trim();
      time = timeEl ? timeEl.innerText.trim() : '';
      likes = likeEl ? likeEl.innerText.trim() : '';
    } else {
      // v2.4.0 兜底：innerText 行解析
      const innerText = item.innerText || '';
      const lines = innerText.split('\n').map(l => l.trim()).filter(Boolean);

      if (lines.length >= 2) {
        // 第1行通常是作者名（排除 "..." 和作者标签）
        author = lines[0];
        if (author === '...' || author === '作者' || /^(回复|分享|关注)$/.test(author)) {
          author = '';
        }

        // 跳过 "..." 行找到正文
        let textStartIdx = 1;
        if (lines[1] === '...') textStartIdx = 2;

        // 时间行：匹配 "X小时前"、"X天前"、"昨天"、"刚刚" 等
        let timeIdx = -1;
        for (let i = textStartIdx; i < lines.length; i++) {
          if (/小时前|天前|分钟前|昨天|前天|刚刚|周前/.test(lines[i])) {
            timeIdx = i;
            time = lines[i];
            break;
          }
        }

        // 评论文本：textStartIdx 到 timeIdx 之间的行（排除 emoji-only 行）
        if (timeIdx > textStartIdx) {
          text = lines.slice(textStartIdx, timeIdx)
            .filter(l => !/^[\uD800-\uDBFF\uDC00-\uDFFF\u2600-\u27BF\u0023\u20E3]*$/.test(l))
            .join(' ');
        } else {
          text = lines.slice(textStartIdx).find(l => l.length > 2 && !/^[\d.]+[万亿]?$/.test(l) && !/^(回复|分享|关注|举报)$/.test(l)) || '';
        }

        // 点赞数：时间行之后的纯数字
        if (timeIdx > 0 && timeIdx + 1 < lines.length) {
          const likeCandidate = lines[timeIdx + 1];
          if (/^\d+$/.test(likeCandidate)) likes = likeCandidate;
        }
      }
    }

    const hasSubReply = expandEl ? true : false;
    const replyBtn = item.querySelector('[class*="reply"], span');

    if (text.length >= 2 && author.length >= 1) {
      comments.push({
        author,
        text: text.substring(0, 150),
        likes,
        time,
        hasSubReply,
        hasReplyBtn: !!replyBtn
      });
    }
  });

  return { total: comments.length, comments: comments.slice(0, 100) };
};

// ─────────────────────────────────────────────
// [6] 滚动评论区（v2.3.0 重写 — WheelEvent 驱动懒加载）
//
// ⚠️ v2.3.0 关键修复：
//   - 抖音评论区使用虚拟滚动，直接赋值 scrollTop 无效（不触发懒加载）
//   - 必须用 WheelEvent 模拟鼠标滚轮，才能触发评论懒加载
// ─────────────────────────────────────────────
const scrollCommentArea = () => {
  const box = document.querySelector('.comment-mainContent')
    || document.querySelector('[class*="commentList"]')
    || document.querySelector('[class*="commentContainer"]')
    || document.querySelector('[class*="comment-list"]')
    || document.querySelector('[class*="CommentList"]');

  if (!box) return { error: 'comment scroll area not found' };

  const rect = box.getBoundingClientRect();
  const centerX = rect.left + rect.width / 2;
  const centerY = rect.top + rect.height / 2;

  // 用 WheelEvent 模拟鼠标滚轮（scrollTop 赋值对虚拟滚动无效）
  box.dispatchEvent(new WheelEvent('wheel', {
    bubbles: true,
    cancelable: true,
    clientX: centerX,
    clientY: centerY,
    deltaY: 800,
    wheelDelta: -800
  }));

  return {
    scrollTop: box.scrollTop,
    scrollHeight: box.scrollHeight,
    clientHeight: box.clientHeight,
    canScrollMore: box.scrollTop + box.clientHeight < box.scrollHeight - 10,
    method: 'WheelEvent',
    centerX: Math.round(centerX),
    centerY: Math.round(centerY)
  };
};

// ─────────────────────────────────────────────
// [7] 查找评论并点击回复按钮（只点击，不等待）
// ─────────────────────────────────────────────
const findAndClickReply = (targetText) => {
  const walker = document.createTreeWalker(
    document.querySelector('.comment-mainContent') || document.body,
    NodeFilter.SHOW_TEXT
  );

  let node;
  while ((node = walker.nextNode())) {
    const trimmed = node.textContent.trim();
    if (trimmed === targetText || trimmed.startsWith(targetText)) {
      let container = node.parentElement;
      for (let i = 0; i < 10; i++) {
        if (!container) break;

        const allSpans = container.querySelectorAll('span, div, button, a');
        let replyBtn = null;

        for (const el of allSpans) {
          if (el.innerText.trim() === '回复'
              && el.children.length === 0
              && el.offsetParent !== null) {
            replyBtn = el;
          }
        }

        if (replyBtn) {
          replyBtn.click();
          return {
            success: true,
            message: 'clicked reply button for: ' + targetText.substring(0, 30)
          };
        }

        container = container.parentElement;
      }

      return {
        success: false,
        message: 'reply button not found in comment container for: ' + targetText.substring(0, 30)
      };
    }
  }

  return {
    success: false,
    message: 'comment text not found: ' + targetText.substring(0, 30)
  };
};

// ─────────────────────────────────────────────
// [8] 向回复输入框输入文本（v2.1.0 重要更新）
//
// ⚠️【重要】此函数使用 execCommand('insertText')，
// 在某些情况下会导致 React Draft.js 组件崩溃（评论区 DOM 卸载）。
//
// 推荐方案：
//   - 优先使用 MCP 的 type_text 工具（模拟真实键盘输入）
//   - 如果用 evaluate_script，需要在 click 回复按钮后、文本为空时调用
//
// AI 使用流程（推荐）：
//   Step 1: findAndClickReply → evaluate_script
//   Step 2: type_text → MCP 工具（不用 evaluate_script）
//   Step 3: press_key "Enter" → MCP 工具（提交）
// ─────────────────────────────────────────────
const typeReply = (text) => {
  const input = document.querySelector(
    '.public-DraftEditor-content[role="combobox"], ' +
    '[role="combobox"].focused, ' +
    '[role="combobox"][contenteditable="true"]'
  );

  if (!input) {
    return { success: false, message: 'reply input not found — React may not have rendered yet, retry after a short delay' };
  }

  if (!input.offsetParent && document.activeElement !== input) {
    return { success: false, message: 'reply input not visible/focused' };
  }

  input.focus();
  document.execCommand('insertText', false, text);

  return {
    success: true,
    message: 'text inserted via execCommand: ' + text.substring(0, 30),
    currentText: (input.innerText || '').substring(0, 50)
  };
};

// ─────────────────────────────────────────────
// [7.5] 等待回复输入框就绪
// ─────────────────────────────────────────────
const waitForReplyInput = () => {
  const input = document.querySelector(
    '.public-DraftEditor-content[role="combobox"], ' +
    '[role="combobox"].focused, ' +
    '[role="combobox"][contenteditable="true"]'
  );

  if (!input) {
    return { found: false };
  }

  return {
    found: true,
    focused: document.activeElement === input,
    visible: input.offsetParent !== null,
    className: (input.className || '').toString().substring(0, 60)
  };
};

// ─────────────────────────────────────────────
// [9] 提交回复（v2.1.0 重写）
//
// ⚠️ 关键发现（2026-04-04 实测）：
//   - 抖音评论输入框是 Draft.js（React），聚焦时发送按钮（.WFB7wUOX）被隐藏
//   - 正确的提交方式：直接按 Enter 键
//   - Ctrl+Enter 无效，点击按钮也无效（聚焦时不可见）
//   - ⚠️【重要】不要用 evaluate_script 的 document.dispatchEvent 模拟键盘事件，
//     会导致 React Draft.js 组件崩溃、评论区 DOM 卸载
//   - 正确做法：用 MCP 的 press_key 工具按 Enter 键
//
// AI 使用说明：
//   1. findAndClickReply → evaluate_script（只点击）
//   2. type_text → MCP type_text 工具（不用 evaluate_script）
//   3. submitReply → MCP press_key "Enter"（不用 evaluate_script）
// ─────────────────────────────────────────────
const submitReply = () => {
  // 检查输入框是否有内容
  const input = document.querySelector('[role="combobox"][contenteditable="true"]');
  if (!input) {
    return { success: false, message: 'reply input not found' };
  }

  const text = (input.innerText || '').trim();
  if (text.length === 0) {
    return { success: false, message: 'reply input is empty, nothing to submit' };
  }

  // ⚠️ 不要在这里模拟键盘事件！
  // 用 MCP 的 press_key "Enter" 来提交
  // 这里只返回状态，让 AI 调用 MCP press_key
  return {
    success: true,
    message: 'input has content, use MCP press_key "Enter" to submit',
    hasContent: true,
    textPreview: text.substring(0, 30)
  };
};

// ─────────────────────────────────────────────
// [9.1] 检查回复是否已提交成功
// ─────────────────────────────────────────────
const checkReplySubmitted = () => {
  const input = document.querySelector('[role="combobox"][contenteditable="true"]');
  const fc = document.querySelector('.comment-input-container-focus');
  const commentMain = document.querySelector('.comment-mainContent');

  // 如果输入框文本为空且焦点容器还在，说明提交成功
  const text = input ? (input.innerText || '').trim() : '';
  if (text.length === 0 && fc) {
    return {
      submitted: true,
      message: 'reply appears to have been submitted (input is empty)',
      commentAreaExists: !!commentMain
    };
  }

  // 如果评论区消失了，可能是提交后刷新
  if (!commentMain) {
    return { submitted: true, message: 'comment area gone after submit (likely refreshed)' };
  }

  return {
    submitted: false,
    message: 'reply still in input, not yet submitted',
    textLength: text.length
  };
};

// ─────────────────────────────────────────────
// [10] 提取视频信息（v2.4.0 加固 — 限定视频详情区域）
//
// ⚠️ v2.4.0 修复（2026-06-18）：
//   - h1/h2 裸选择器曾匹配到侧边栏导航（"搜索""我的"）
//   - 增加视频详情容器 scoping，优先在 [class*="videoInfo"]/[class*="detail"] 内搜索
//   - 排除 <a> 标签内的 h1/h2（导航链接）
// ─────────────────────────────────────────────
const extractVideoInfo = () => {
  // v2.4.0: 先找视频详情容器，限定搜索范围
  const videoContainer = document.querySelector(
    '[class*="videoInfo"], [class*="videoDetail"], ' +
    '[class*="detailContainer"], [class*="detail-wrapper"], ' +
    '[class*="video-meta"], [class*="videoMeta"], ' +
    '[class*="playerContainer"]'
  );

  const searchRoot = videoContainer || document;

  // 标题：data-e2e → class 关键词 → h1 → h2 兜底（排除 <a> 内）
  const titleEl = searchRoot.querySelector(
    '[data-e2e="video-title"], ' +
    '[class*="videoDesc"], [class*="videoTitle"], .descText, ' +
    '[class*="desc"], [class*="title"]'
  );
  // h1/h2 兜底：排除 <a> 标签内的（导航栏）
  let hTitle = null;
  if (!titleEl) {
    const allH = searchRoot.querySelectorAll('h1, h2');
    for (const h of allH) {
      if (!h.closest('a') && h.innerText.trim().length > 5) {
        hTitle = h;
        break;
      }
    }
  }

  // 作者：data-e2e → class 关键词 → meta 标签兜底
  const authorEl = document.querySelector(
    '[data-e2e="video-author-name"], ' +
    '[class*="authorName"], [class*="nickName"], ' +
    '[class*="authorNick"], [class*="nick"], ' +
    'a[href*="/@"] span, a[href*="/user/"] span'
  );

  // 点赞：data-e2e → class 关键词 → 扫描文本兜底
  const likeEl = document.querySelector(
    '[data-e2e="video-like-count"], ' +
    '[class*="likeCount"], [class*="diggCount"], ' +
    '[class*="digg"], [class*="like-count"]'
  );

  // 评论数
  const commentEl = document.querySelector(
    '[data-e2e="video-comment-count"], [class*="commentCount"]'
  );

  const urlMatch = window.location.href.match(/video\/(\d+)/);

  // v2.2.0 新增：提取发布时间
  const timeResult = extractVideoPublishTime();

  const title = (titleEl || hTitle) ? (titleEl || hTitle).innerText.trim().substring(0, 100) : '';
  const author = authorEl ? authorEl.innerText.trim() : '';
  const likes = likeEl ? likeEl.innerText.trim() : '';
  const comments = commentEl ? commentEl.innerText.trim() : '';

  return {
    title: title || 'unknown',
    author: author || 'unknown',
    likes: likes || 'unknown',
    comments: comments || 'unknown',
    publishTime: timeResult.success ? timeResult.raw : null,
    videoId: urlMatch ? urlMatch[1] : null,
    url: window.location.href,
    _selectors: {
      titleFound: !!(titleEl || hTitle),
      authorFound: !!authorEl,
      likesFound: !!likeEl
    }
  };
};

// ─────────────────────────────────────────────
// [11] 检测验证码/安全弹窗（v2.4.0 修复 slider 误报）
//
// ⚠️ v2.4.0 修复（2026-06-18）：
//   - [class*="slider"] 太宽泛，会匹配视频进度条
//   - 改为精确匹配 captcha/verify 容器内的 slider
// ─────────────────────────────────────────────
const checkCaptcha = () => {
  const body = document.body.innerText;
  const hasCaptcha = body.includes('验证码') || body.includes('短信验证') || body.includes('安全验证');
  // v2.4.0: 只匹配验证码弹窗内的 slider，排除视频进度条
  const hasSlider = !!document.querySelector(
    '[class*="captcha"][class*="slider"], ' +
    '[class*="verify"][class*="slider"], ' +
    '[class*="captcha"] [class*="slider"], ' +
    '[class*="verify"] [class*="slider"]'
  );
  const hasBlock = body.includes('操作频繁') || body.includes('账号异常');

  return {
    hasCaptcha,
    hasSlider,
    hasBlock,
    safe: !hasCaptcha && !hasSlider && !hasBlock
  };
};

// ─────────────────────────────────────────────
// [11.5] V3 新增：增强验证码检测 + 登录状态检测
// ─────────────────────────────────────────────
const checkLoginStatus = () => {
  const isLoggedIn = !document.querySelector('[class*="loginPanel"], [class*="loginButton"], [data-e2e="login-button"]')
    && !document.body.innerText.includes('登录');
  const hasAvatar = !!document.querySelector('[class*="avatar"], [class*="userAvatar"]');
  return { isLoggedIn, hasAvatar };
};

// ─────────────────────────────────────────────
// [12] 一站式批量扫描 + 滚动
// ─────────────────────────────────────────────
const batchScan = (keywords, rounds = 3) => {
  const allMatches = [];
  const seenComments = new Set();

  for (let i = 0; i < rounds; i++) {
    const result = extractComments();
    if (result.error) continue;

    const comments = result.comments || [];
    comments.forEach(c => {
      const key = c.author + '|' + c.text;
      if (seenComments.has(key)) return;
      seenComments.add(key);

      for (const kw of keywords) {
        if (c.text.includes(kw)) {
          allMatches.push({
            keyword: kw,
            comment: c.text,
            author: c.author,
            likes: c.likes
          });
          break;
        }
      }
    });

    scrollCommentArea();
  }

  return {
    totalScanned: seenComments.size,
    matches: allMatches.slice(0, 50)
  };
};

// ─────────────────────────────────────────────
// [辅助] 获取输入框当前状态
// ─────────────────────────────────────────────
const getInputBoxStatus = () => {
  const input = document.querySelector(
    '[role="combobox"][aria-haspopup="listbox"], ' +
    '[class*="commentInput"] [role="textbox"], ' +
    '[contenteditable="true"][class*="comment"]'
  );

  if (!input) return { found: false };

  return {
    found: true,
    tagName: input.tagName,
    role: input.getAttribute('role'),
    value: input.value || input.innerText || '',
    focused: document.activeElement === input,
    visible: input.offsetParent !== null,
    placeholder: input.getAttribute('placeholder') || input.getAttribute('aria-label') || ''
  };
};

// ─────────────────────────────────────────────
// [13] v2.2.0 新增：提取视频发布时间
// ─────────────────────────────────────────────
const extractVideoPublishTime = () => {
  // 方法1：视频标题旁边的日期
  const timeEl = document.querySelector(
    '[data-e2e="video-publish-time"], [class*="publishTime"], [class*="createTime"], [class*="date"]'
  );
  if (timeEl) {
    const t = timeEl.innerText.trim();
    if (t) return { success: true, raw: t };
  }

  // 方法2：视频描述区的时间信息
  const descEl = document.querySelector('[class*="videoDesc"], [class*="videoTitle"], .descText');
  if (descEl) {
    // 视频描述中通常包含发布时间，格式如 "2026-04-01" 或 "3天前"
    const timeMatch = descEl.innerText.match(/(\d{4}[-/]\d{1,2}[-/]\d{1,2})/);
    if (timeMatch) return { success: true, raw: timeMatch[1] };

    const agoMatch = descEl.innerText.match(/(\d+[\u4e00-\u9fff]+前)/);
    if (agoMatch) return { success: true, raw: agoMatch[1] };
  }

  // 方法3：评论区顶部的视频时间标签
  const infoEls = document.querySelectorAll('[class*="videoInfo"], [class*="authorInfo"] span, [class*="videoMeta"] span');
  for (const el of infoEls) {
    const t = el.innerText.trim();
    if (/^\d{4}[-/]\d{1,2}[-/]\d{1,2}$/.test(t) || /^\d+[\u4e00-\u9fff]+前$/.test(t) || /^\d+小时前$/.test(t) || /^\d+天前$/.test(t) || /^昨天/.test(t) || /^前天/.test(t)) {
      return { success: true, raw: t };
    }
  }

  return { success: false, message: 'video publish time not found' };
};

// ─────────────────────────────────────────────
// [14] v2.2.0 新增：将中文相对时间转为小时数
// 用于新鲜度判断（>168小时 = 超过1周）
// ─────────────────────────────────────────────
const parseTimeAgo = (timeStr) => {
  if (!timeStr) return null;

  // 精确日期：2026-04-01
  const dateMatch = timeStr.match(/(\d{4})[-/](\d{1,2})[-/](\d{1,2})/);
  if (dateMatch) {
    const then = new Date(parseInt(dateMatch[1]), parseInt(dateMatch[2]) - 1, parseInt(dateMatch[3]));
    const hours = Math.floor((Date.now() - then.getTime()) / 3600000);
    return { hours, days: Math.floor(hours / 24), text: timeStr };
  }

  // 相对时间
  const num = timeStr.match(/(\d+)/);
  const n = num ? parseInt(num[1]) : 0;

  if (/分钟前/.test(timeStr)) return { hours: 0, days: 0, text: timeStr };
  if (/小时前/.test(timeStr)) return { hours: n, days: 0, text: timeStr };
  if (/天前/.test(timeStr)) return { hours: n * 24, days: n, text: timeStr };
  if (/周前|个星期前/.test(timeStr)) return { hours: n * 168, days: n * 7, text: timeStr };
  if (/月前/.test(timeStr)) return { hours: n * 720, days: n * 30, text: timeStr };
  if (/年前/.test(timeStr)) return { hours: n * 8760, days: n * 365, text: timeStr };
  if (/昨天/.test(timeStr)) return { hours: 24, days: 1, text: timeStr };
  if (/前天/.test(timeStr)) return { hours: 48, days: 2, text: timeStr };
  if (/刚刚/.test(timeStr)) return { hours: 0, days: 0, text: timeStr };

  return { hours: null, text: timeStr, message: 'unrecognized format' };
};

// ─────────────────────────────────────────────
// [15] v2.3.0 新增：页面诊断 — 选择器失效时的兜底分析
//
// 用途：当任何函数返回 error 或数据为空时，调用此函数
// 返回当前页面的结构截面，辅助 AI 判断选择器怎么改
//
// 触发时机（AI 必读）：
//   - extractVideoList() 返回 count: 0
//   - extractComments() 返回 error 或 total: 0
//   - extractVideoInfo() 返回 title: "unknown"
//   - 任何操作找不到元素时
//
// 返回信息：
//   - pageType: 当前是哪种页面（搜索/视频/首页）
//   - topClassNames: 页面顶层元素 class 名片段（帮助找新选择器）
//   - videoLinks: 找到的视频链接数量
//   - commentArea: 评论区是否存在
//   - h1/h2: 标题标签内容
// ─────────────────────────────────────────────
const diagnosePage = () => {
  const url = window.location.href;

  // 判断页面类型
  let pageType = 'unknown';
  if (url.includes('/search/')) pageType = 'search';
  else if (url.includes('/video/')) pageType = 'video';
  else if (url === 'https://www.douyin.com/' || url.includes('douyin.com/?')) pageType = 'home';
  else if (url.includes('/user/')) pageType = 'user';

  // 收集顶层容器 class 名（帮助发现新选择器）
  const topDivs = Array.from(document.querySelectorAll('body > div, body > div > div, body > div > div > div'));
  const topClassNames = topDivs
    .slice(0, 20)
    .map(el => (el.className || '').toString().substring(0, 60))
    .filter(c => c.length > 0);

  // 搜索结果容器探测
  const searchContainerCandidates = {};
  const searchSelectors = [
    '[class*="search"]',
    '[class*="Search"]',
    '[class*="result"]',
    '[class*="Result"]',
    '[class*="video-list"]',
    '[class*="videoList"]',
    '[class*="feed"]',
    '[class*="Feed"]'
  ];
  for (const sel of searchSelectors) {
    const count = document.querySelectorAll(sel).length;
    if (count > 0) searchContainerCandidates[sel] = count;
  }

  // 视频链接
  const videoLinks = document.querySelectorAll('a[href*="/video/"]').length;

  // 评论区探测
  const commentSelectors = {
    '.comment-mainContent': !!document.querySelector('.comment-mainContent'),
    '[class*="commentList"]': !!document.querySelector('[class*="commentList"]'),
    '[class*="comment-list"]': !!document.querySelector('[class*="comment-list"]'),
    '[class*="CommentList"]': !!document.querySelector('[class*="CommentList"]'),
    '[data-e2e="comment-item"]': !!document.querySelector('[data-e2e="comment-item"]')
  };

  // h1/h2 内容
  const h1 = document.querySelector('h1');
  const h2 = document.querySelector('h2');

  // 页面文本摘要（前500字）
  const bodyText = (document.body.innerText || '').substring(0, 300).replace(/\n+/g, ' ');

  return {
    pageType,
    url: url.substring(0, 100),
    videoLinks,
    h1: h1 ? h1.innerText.trim().substring(0, 80) : null,
    h2: h2 ? h2.innerText.trim().substring(0, 80) : null,
    commentArea: commentSelectors,
    searchContainerCandidates,
    topClassNames: topClassNames.slice(0, 10),
    bodyTextPreview: bodyText,
    title: document.title.substring(0, 60)
  };
};

// ─────────────────────────────────────────────
// [16] v2.3.0 新增：批量探测选择器
//
// 用途：快速测试一批选择器哪个有效，辅助选择器调试
// 入参：selectors 数组
// 示例：probeSelector(['[class*="search"]', '.AMqhOzPC', 'h1'])
// ─────────────────────────────────────────────
const probeSelector = (selectors) => {
  const results = {};
  for (const sel of selectors) {
    try {
      const els = document.querySelectorAll(sel);
      results[sel] = {
        count: els.length,
        firstText: els[0] ? (els[0].innerText || '').trim().substring(0, 60) : null,
        firstClass: els[0] ? (els[0].className || '').toString().substring(0, 60) : null
      };
    } catch (e) {
      results[sel] = { error: e.message };
    }
  }
  return results;
};
