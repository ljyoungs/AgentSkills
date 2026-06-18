#!/usr/bin/env python3
"""
抖音引流-psy V3 — 配置管理工具

V3 新增功能：
  - 行业预设模板库（6 大行业 + 通用）
  - 配置导入/导出（跨机器复制配置）
  - 初始化状态管理
  - 话题增删改查

命令：
  python config_manager.py init           # 初始化默认配置
  python config_manager.py show           # 显示当前配置
  python config_manager.py stats          # 显示今日统计
  python config_manager.py templates       # 显示可用行业模板
  python config_manager.py export          # 导出配置为 JSON
  python config_manager.py import-config <文件路径>  # 导入配置
  python config_manager.py check           # 检查初始化状态
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path

# ─────────────────────────────────────────────
# 路径定义
# ─────────────────────────────────────────────
SKILL_DIR = Path(__file__).parent.parent
CONFIG_FILE = SKILL_DIR / "config.json"
DATA_DIR = SKILL_DIR / "data"
DAILY_SUMMARY_DIR = DATA_DIR / "daily_summary"
REPLIED_FILE = DATA_DIR / "replied.json"  # v2.2.0 新增：已回复记录

# ─────────────────────────────────────────────
# 默认配置
# ─────────────────────────────────────────────
DEFAULT_CONFIG = {
    "_version": "3.0",
    "_initialized": False,
    "topics": [],
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
        "auto_mode": False
    },
    "data_dir": "data",
    "log_level": "info"
}


# ─────────────────────────────────────────────
# 行业预设模板库（V3 核心新增）
# ─────────────────────────────────────────────
INDUSTRY_TEMPLATES = {
    "旅游": {
        "keywords": ["求攻略", "路线", "怎么去", "求推荐", "几月去好", "避坑", "自驾", "行程安排", "第一次去", "怎么玩"],
        "reply_templates": [
            "刚从{city}回来，整理了一份超详细攻略，需要的可以私信我~",
            "推荐几个{city}必去的地方，篇幅有限私信发你完整版",
            "{city}吃喝玩乐全攻略我有整理，私信免费分享给你",
            "避坑指南+省钱攻略都有，私信发你~"
        ]
    },
    "教育": {
        "keywords": ["怎么学", "提分", "零基础", "求教程", "不及格", "辅导", "方法", "资料", "自学", "报班"],
        "reply_templates": [
            "整理了一套超全的{subject}学习资料，私信免费分享~",
            "我当初也是零基础，后来找到了方法，私信告诉你",
            "推荐几个好用的{subject}学习资源，私信发你链接"
        ]
    },
    "电商": {
        "keywords": ["怎么选", "哪个好", "求推荐", "性价比", "靠谱吗", "入手", "好用吗", "购买", "渠道"],
        "reply_templates": [
            "用了{duration}了，亲测好用，私信告诉你哪里买更划算",
            "对比了好多款，最后选了这个，私信分享选购攻略",
            "这个确实不错，私信告诉你我的使用体验和购买渠道"
        ]
    },
    "健身": {
        "keywords": ["怎么减", "求计划", "饮食", "零基础", "体重", "瘦腿", "增肌", "马甲线", "蛋白", "有氧"],
        "reply_templates": [
            "{months}个月减了{weight}斤，方法很简单，私信分享~",
            "整理了一份适合新手的健身计划，私信免费发你",
            "其实核心就几个动作+饮食控制，私信告诉你具体方法"
        ]
    },
    "美妆": {
        "keywords": ["怎么用", "避坑", "求推荐", "适合", "敏感肌", "平价", "测评", "好用", "色号", "肤质"],
        "reply_templates": [
            "用了{duration}，真实感受告诉你，私信分享~",
            "踩过很多坑才找到的，私信告诉你好不好",
            "整理了一份平价好用的清单，私信发你"
        ]
    },
    "本地生活": {
        "keywords": ["好吃的", "求推荐", "必去", "排队", "优惠", "聚餐", "打卡", "探店", "周末", "遛娃"],
        "reply_templates": [
            "整理了一份{city}美食地图，私信发你~",
            "这家确实好吃，还知道几家隐藏好店，私信告诉你",
            "{city}本地人推荐的，私信分享完整清单"
        ]
    },
    "知识付费": {
        "keywords": ["怎么入门", "求资料", "学习", "课程", "教程", "免费", "资源", "赚钱", "副业", "变现"],
        "reply_templates": [
            "整理了一套{topic}入门资料包，私信免费分享~",
            "我也是从零开始的，走过很多弯路，私信告诉你正确方法",
            "这个我有经验，整理了核心笔记，私信发你"
        ]
    }
}

# 通用模板（兜底）
GENERIC_TEMPLATE = {
    "keywords": ["求推荐", "怎么选", "求攻略", "有没有", "推荐一下", "分享一下"],
    "reply_templates": [
        "整理了一份超详细的资料，需要的可以私信我~",
        "亲测好用，篇幅有限私信发你完整版",
        "这个我有经验，私信免费分享给你"
    ]
}


# ─────────────────────────────────────────────
# 配置读写
# ─────────────────────────────────────────────
def load_config():
    """加载配置文件，不存在则创建默认配置"""
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            config = json.load(f)
        # 确保有 V3 字段
        config.setdefault("_version", "3.0")
        config.setdefault("_initialized", False)
        config.setdefault("topics", [])
        config.setdefault("global_settings", DEFAULT_CONFIG["global_settings"].copy())
        return config
    else:
        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG.copy()


def save_config(config):
    """保存配置到文件"""
    CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)
    print(f"配置已保存到 {CONFIG_FILE}")


# ─────────────────────────────────────────────
# 行业模板操作
# ─────────────────────────────────────────────
def get_industry_template(industry_name):
    """根据行业名称获取预设模板，支持模糊匹配"""
    for key, template in INDUSTRY_TEMPLATES.items():
        if key in industry_name or industry_name in key:
            return {"industry": key, **template}
    return {"industry": "通用", **GENERIC_TEMPLATE}


def show_templates():
    """显示所有可用的行业模板"""
    print("\n可用的行业预设模板：")
    print("=" * 50)
    for i, (name, tmpl) in enumerate(INDUSTRY_TEMPLATES.items(), 1):
        print(f"\n  [{i}] {name}")
        print(f"      匹配关键词: {', '.join(tmpl['keywords'][:5])}...")
        print(f"      回复模板数: {len(tmpl['reply_templates'])}")
    print(f"\n  [0] 通用（适合所有领域）")
    print()


def create_topic_from_template(industry, city_or_subject="", extra_keywords=None):
    """根据行业模板创建话题配置"""
    tmpl = get_industry_template(industry)
    keywords = list(tmpl["keywords"])
    if extra_keywords:
        keywords.extend(k for k in extra_keywords if k not in keywords)

    templates = list(tmpl["reply_templates"])
    # 替换占位符
    placeholders = {
        "{city}": city_or_subject or "那里",
        "{subject}": city_or_subject or "这个",
        "{topic}": city_or_subject or "这个领域",
        "{duration}": "一段时间",
        "{months}": "3",
        "{weight}": "20",
    }
    templates_resolved = []
    for t in templates:
        resolved = t
        for key, val in placeholders.items():
            resolved = resolved.replace(key, val)
        templates_resolved.append(resolved)

    topic = {
        "name": f"{industry}引流",
        "search_keyword": f"{industry} {city_or_subject}" if city_or_subject else industry,
        "enabled": True,
        "keywords": keywords,
        "reply_templates": templates_resolved,
        "max_videos": 3,
        "max_replies_per_video": 1,
        "max_daily_replies": 15
    }
    return topic


# ─────────────────────────────────────────────
# 初始化状态管理
# ─────────────────────────────────────────────
def is_initialized():
    """检查是否已完成初始化"""
    config = load_config()
    return config.get("_initialized", False)


def mark_initialized():
    """标记为已初始化"""
    config = load_config()
    config["_initialized"] = True
    save_config(config)


def check_status():
    """检查配置状态"""
    config = load_config()
    print("\n" + "=" * 50)
    print("抖音引流-psy V3 状态检查")
    print("=" * 50)

    initialized = config.get("_initialized", False)
    topics = config.get("topics", [])
    has_topics = len(topics) > 0
    has_active = any(t.get("enabled", True) for t in topics)

    print(f"\n  初始化状态: {'已完成' if initialized else '未初始化'}")
    print(f"  话题总数: {len(topics)}")
    print(f"  启用话题: {sum(1 for t in topics if t.get('enabled', True))}")
    print(f"  版本: {config.get('_version', '未知')}")

    if not has_topics:
        print("\n  状态: 需要配置话题才能开始使用")
        print("  请运行: python config_manager.py templates （查看可用行业模板）")
    elif not has_active:
        print("\n  状态: 所有话题已禁用，请启用至少一个话题")
    else:
        print("\n  状态: 就绪，可以开始使用")

    return {
        "initialized": initialized,
        "has_topics": has_topics,
        "has_active": has_active
    }


# ─────────────────────────────────────────────
# 配置导入导出（V3 核心新增）
# ─────────────────────────────────────────────
def export_config(output_path=None):
    """导出当前配置为 JSON 文件（用于跨机器复制）"""
    config = load_config()

    # 只导出业务配置，不导出内部状态
    export_data = {
        "version": config.get("_version", "3.0"),
        "topics": config.get("topics", []),
        "global_settings": config.get("global_settings", {}),
        "exported_at": datetime.now().isoformat()
    }

    if output_path is None:
        output_path = SKILL_DIR / "config_export.json"

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(export_data, f, ensure_ascii=False, indent=2)

    print(f"配置已导出到: {output_path}")
    print(f"\n导出内容:")
    print(f"  话题数: {len(export_data['topics'])}")
    print(f"  导出时间: {export_data['exported_at']}")
    print(f"\n使用方法:")
    print(f"  1. 将 config_export.json 复制到目标机器")
    print(f"  2. 运行: python config_manager.py import-config config_export.json")


def import_config(json_path):
    """从 JSON 文件导入配置（用于跨机器复制）"""
    path = Path(json_path)
    if not path.exists():
        print(f"文件不存在: {json_path}")
        return False

    try:
        with open(path, "r", encoding="utf-8") as f:
            imported = json.load(f)
    except json.JSONDecodeError as e:
        print(f"JSON 解析失败: {e}")
        return False

    config = load_config()

    # 合并 topics（按名称去重）
    if "topics" in imported:
        existing_names = {t.get("name") for t in config.get("topics", [])}
        added = 0
        for topic in imported["topics"]:
            if topic.get("name") not in existing_names:
                config.setdefault("topics", []).append(topic)
                added += 1
        print(f"导入话题: {added} 个新话题")
    else:
        print("导入文件中无 topics 字段")

    # 覆盖 global_settings
    if "global_settings" in imported:
        config["global_settings"] = imported["global_settings"]
        print("全局设置已更新")

    # 标记为已初始化
    if config.get("topics"):
        config["_initialized"] = True

    save_config(config)
    return True


# ─────────────────────────────────────────────
# 话题管理
# ─────────────────────────────────────────────
def show_config():
    """显示当前配置"""
    config = load_config()
    print("\n" + "=" * 50)
    print("抖音引流-psy V3 配置")
    print("=" * 50)

    if not config.get("topics"):
        print("\n  暂无话题配置。")
        print("  请运行: python config_manager.py templates 查看可用行业模板")
        print("  或通过 AI 对话配置：对 AI 说「帮我设置抖音引流」")
        return

    print("\n话题列表：")
    for i, topic in enumerate(config["topics"]):
        status = "[ON]" if topic.get("enabled", True) else "[OFF]"
        print(f"  {status} [{i + 1}] {topic['name']}")
        print(f"      搜索关键词: {topic['search_keyword']}")
        print(f"      匹配关键词: {', '.join(topic['keywords'][:8])}")
        if len(topic['keywords']) > 8:
            print(f"                   ...等 {len(topic['keywords'])} 个")
        print(f"      回复模板数: {len(topic.get('reply_templates', []))}")
        print(f"      单次最多视频: {topic.get('max_videos', 3)}")
        print(f"      单视频最多回复: {topic.get('max_replies_per_video', 1)}")
        print(f"      日回复上限: {topic.get('max_daily_replies', 15)}")

    gs = config.get("global_settings", {})
    print("\n全局设置：")
    print(f"  日回复上限: {gs.get('daily_reply_limit', 30)}")
    print(f"  回复间隔: {gs.get('reply_interval_min_seconds', 45)}-{gs.get('reply_interval_max_seconds', 120)}秒")
    print(f"  视频观看: {gs.get('video_watch_min_seconds', 15)}-{gs.get('video_watch_max_seconds', 45)}秒")
    print(f"  操作间隔: {gs.get('action_delay_min_seconds', 3)}-{gs.get('action_delay_max_seconds', 8)}秒")
    print(f"  活跃时段: {gs.get('active_hours_start', 9):02d}:00-{gs.get('active_hours_end', 23):02d}:00")
    print(f"  评论滚动轮数: {gs.get('comment_scroll_rounds', 3)}")
    mode = "全自动" if gs.get("auto_mode", False) else "半自动（每步确认）"
    print(f"  运行模式: {mode}")
    print(f"  架构版本: V3 (标准化交付)")
    print()


def add_topic_interactive():
    """交互式添加新话题"""
    config = load_config()

    print("\n+ 添加新话题")
    print("-" * 30)

    name = input("话题名称: ").strip()
    if not name:
        print("名称不能为空")
        return

    keyword = input("搜索关键词: ").strip()
    if not keyword:
        print("关键词不能为空")
        return

    print("\n输入匹配关键词（逗号分隔，回车确认）:")
    keywords_str = input("  > ").strip()
    keywords = [k.strip() for k in keywords_str.split(",") if k.strip()] if keywords_str else []

    print("\n输入回复模板（每行一个，空行结束）:")
    templates = []
    while True:
        tmpl = input("  > ").strip()
        if not tmpl:
            break
        templates.append(tmpl)

    if not templates:
        print("至少需要一个回复模板")
        return

    topic = {
        "name": name,
        "search_keyword": keyword,
        "enabled": True,
        "keywords": keywords,
        "reply_templates": templates,
        "max_videos": 3,
        "max_replies_per_video": 1,
        "max_daily_replies": 15
    }

    config["topics"].append(topic)
    if len(config["topics"]) > 0:
        config["_initialized"] = True
    save_config(config)
    print(f"话题 [{name}] 已添加")


# ─────────────────────────────────────────────
# 防重复模块（v2.2.0 新增）
# ─────────────────────────────────────────────
def _load_replied():
    """加载已回复记录"""
    if REPLIED_FILE.exists():
        with open(REPLIED_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"replies": []}


def _save_replied(data):
    """保存已回复记录"""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(REPLIED_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def add_replied_record(video_id, video_title, video_author, comment_author, comment_text,
                       reply_content, search_keyword, topic_name, video_url=None):
    """添加一条已回复记录"""
    data = _load_replied()

    # 去重：同一视频+同一评论不重复记录
    key = f"{video_id}:{comment_author}:{comment_text[:30]}"
    if any(r.get("key") == key for r in data["replies"]):
        return False  # 已存在

    record = {
        "key": key,
        "video_id": video_id,
        "video_title": video_title[:80],
        "video_author": video_author,
        "video_url": video_url or f"https://www.douyin.com/video/{video_id}",
        "comment_author": comment_author,
        "comment_text": comment_text[:100],
        "reply_content": reply_content[:100],
        "search_keyword": search_keyword,
        "topic_name": topic_name,
        "replied_at": datetime.now().isoformat(),
        "date": datetime.now().strftime("%Y%m%d")
    }
    data["replies"].append(record)

    # 自动清理 30 天前的记录
    _cleanup_old_records(data, days=30)

    _save_replied(data)
    return True


def is_video_replied(video_id):
    """检查视频是否已回复过（任意评论）"""
    data = _load_replied()
    return any(r.get("video_id") == video_id for r in data["replies"])


def is_comment_replied(video_id, comment_author, comment_text):
    """检查特定评论是否已回复过"""
    key = f"{video_id}:{comment_author}:{comment_text[:30]}"
    data = _load_replied()
    return any(r.get("key") == key for r in data["replies"])


def get_replied_video_ids():
    """获取所有已回复过的视频 ID 列表"""
    data = _load_replied()
    return list(set(r.get("video_id") for r in data["replies"] if r.get("video_id")))


def get_today_replied_count():
    """获取今日已回复数量"""
    today = datetime.now().strftime("%Y%m%d")
    data = _load_replied()
    return sum(1 for r in data["replies"] if r.get("date") == today)


def _cleanup_old_records(data, days=30):
    """清理 N 天前的记录"""
    cutoff = datetime.now().strftime("%Y%m%d")
    from datetime import timedelta
    cutoff_date = datetime.now() - timedelta(days=days)
    cutoff_str = cutoff_date.strftime("%Y%m%d")
    data["replies"] = [r for r in data["replies"] if r.get("date", "0") >= cutoff_str]


def show_replied():
    """显示最近已回复记录（默认最近 20 条）"""
    data = _load_replied()
    replies = data.get("replies", [])

    if not replies:
        print("\n  暂无已回复记录")
        return

    # 按时间倒序
    recent = sorted(replies, key=lambda r: r.get("replied_at", ""), reverse=True)[:20]

    print("\n" + "=" * 70)
    print("最近回复记录（最新 20 条）")
    print("=" * 70)

    for i, r in enumerate(recent, 1):
        print(f"\n  [{i}] {r.get('replied_at', '?')[:16]}")
        print(f"      话题: {r.get('topic_name', '?')}  |  搜索: {r.get('search_keyword', '?')}")
        print(f"      视频: {r.get('video_title', '?')[:50]}")
        print(f"      作者: {r.get('video_author', '?')}  |  ID: {r.get('video_id', '?')}")
        print(f"      评论文本: {r.get('comment_text', '?')[:40]}  (by {r.get('comment_author', '?')})")
        print(f"      回复内容: {r.get('reply_content', '?')[:40]}")

    print(f"\n  总计: {len(replies)} 条回复记录")

    # 今日统计
    today_count = get_today_replied_count()
    unique_videos = len(set(r.get("video_id") for r in replies if r.get("video_id")))
    print(f"  今日已回复: {today_count} 条  |  覆盖视频: {unique_videos} 个")
    print()


# ─────────────────────────────────────────────
# Session 管理（v2.2.0 新增）
# ─────────────────────────────────────────────
def save_session(session_data):
    """
    保存一次运行 session。

    session_data 应包含:
      stats: { videos_visited, comments_scanned, comments_matched, replies_sent }
      actions: [{ step, video_id?, video_title?, comment_author?, comment_text?, reply_content?, search_keyword?, topic_name? }]
    """
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    session_id = datetime.now().strftime("%Y%m%d_%H%M%S")

    full_session = {
        "session_id": session_id,
        "version": "3.0",
        "start_time": datetime.now().isoformat(),
        "stats": session_data.get("stats", {}),
        "actions": session_data.get("actions", [])
    }

    path = DATA_DIR / f"session_{session_id}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(full_session, f, ensure_ascii=False, indent=2)

    return session_id, str(path)


def _get_history(days=None):
    """获取历史数据（按天汇总），days=None 表示全部"""
    if not DATA_DIR.exists():
        return []

    daily = {}
    for f in sorted(DATA_DIR.glob("session_*.json")):
        try:
            with open(f, "r", encoding="utf-8") as fh:
                data = json.load(fh)
            stats = data.get("stats", {})
            sid = data.get("session_id", "")
            # 日期从 session_id 提取: 20260404_110000 -> 20260404
            date_str = sid.split("_")[0] if "_" in sid else "unknown"

            if days:
                from datetime import timedelta
                cutoff = (datetime.now() - timedelta(days=days)).strftime("%Y%m%d")
                if date_str < cutoff:
                    continue

            if date_str not in daily:
                daily[date_str] = {
                    "date": date_str,
                    "sessions": 0,
                    "videos_visited": 0,
                    "comments_scanned": 0,
                    "comments_matched": 0,
                    "replies_sent": 0,
                    "details": []
                }
            d = daily[date_str]
            d["sessions"] += 1
            d["videos_visited"] += stats.get("videos_visited", 0)
            d["comments_scanned"] += stats.get("comments_scanned", 0)
            d["comments_matched"] += stats.get("comments_matched", 0)
            d["replies_sent"] += stats.get("replies_sent", 0)

            # 保存每条回复的详情
            for action in data.get("actions", []):
                if action.get("step") == "reply_sent":
                    d["details"].append({
                        "search_keyword": action.get("search_keyword", "?"),
                        "topic_name": action.get("topic_name", "?"),
                        "video_title": action.get("video_title", "?")[:60],
                        "video_author": action.get("video_author", "?"),
                        "video_id": action.get("video_id", "?"),
                        "comment_author": action.get("comment_author", "?"),
                        "comment_text": action.get("comment_text", "?")[:50],
                        "reply_content": action.get("reply_content", "?")[:50],
                        "time": action.get("time", "?")
                    })

        except (json.JSONDecodeError, KeyError):
            pass

    return sorted(daily.values(), key=lambda x: x["date"], reverse=True)


def show_history(days=7):
    """显示历史数据，简洁有用格式"""
    history = _get_history(days)

    if not history:
        print(f"\n  近 {days} 天无运行数据")
        return

    print("\n" + "=" * 70)
    print(f"[*] 引流历史记录（近 {days} 天）")
    print("=" * 70)

    total_replies = 0
    total_videos = 0
    total_scanned = 0
    total_matched = 0

    for day in history:
        d = day["date"]
        # 格式化日期: 20260404 -> 2026-04-04
        pretty_date = f"{d[:4]}-{d[4:6]}-{d[6:8]}" if len(d) == 8 else d

        print(f"\n{'─' * 70}")
        print(f"  [日期] {pretty_date}  |  {day['sessions']} 次运行")
        print(f"     视频: {day['videos_visited']}  |  扫描: {day['comments_scanned']}  |  "
              f"匹配: {day['comments_matched']}  |  回复: {day['replies_sent']}")

        # 每条回复的详情
        if day["details"]:
            for i, detail in enumerate(day["details"], 1):
                print(f"\n     回复 {i}:")
                print(f"       [搜索] \"{detail['search_keyword']}\" -> \"{detail['topic_name']}\"")
                print(f"       [视频] {detail['video_title']}")
                print(f"          作者: {detail['video_author']}  |  ID: {detail['video_id']}")
                print(f"       [评论] [{detail['comment_author']}] {detail['comment_text']}")
                print(f"       [回复] {detail['reply_content']}")

        total_replies += day["replies_sent"]
        total_videos += day["videos_visited"]
        total_scanned += day["comments_scanned"]
        total_matched += day["comments_matched"]

    # 汇总
    print(f"\n{'=' * 70}")
    print(f"  [累计] {total_videos} 视频  |  {total_scanned} 扫描  |  "
          f"{total_matched} 匹配  |  {total_replies} 回复")

    if total_scanned > 0:
        rate = (total_matched / total_scanned * 100)
        print(f"  [效率] 匹配率: {rate:.1f}%  |  回复率: {(total_replies / total_matched * 100) if total_matched > 0 else 0:.1f}%")
    print()


# ─────────────────────────────────────────────
# 统计
# ─────────────────────────────────────────────
def get_today_stats():
    """获取今日统计（优先从 session 文件汇总，兼容 replied.json）"""
    today = datetime.now().strftime("%Y%m%d")

    if not DATA_DIR.exists():
        return None

    total_replies = 0
    total_videos = 0
    total_scanned = 0
    total_matched = 0
    total_snapshots = 0
    sessions = []

    for f in DATA_DIR.glob(f"session_{today}_*.json"):
        try:
            with open(f, "r", encoding="utf-8") as fh:
                data = json.load(fh)
            stats = data.get("stats", {})
            total_replies += stats.get("replies_sent", 0)
            total_videos += stats.get("videos_visited", 0)
            total_scanned += stats.get("comments_scanned", 0)
            total_matched += stats.get("comments_matched", 0)
            total_snapshots += stats.get("snapshots_used", 0)
            sessions.append(data.get("session_id", f.stem))
        except (json.JSONDecodeError, KeyError):
            pass

    # v2.2.0 兼容：如果 session 文件为空但 replied.json 有今日记录
    if total_replies == 0 and REPLIED_FILE.exists():
        total_replies = get_today_replied_count()

    return {
        "date": today,
        "sessions": sessions,
        "videos_visited": total_videos,
        "comments_scanned": total_scanned,
        "comments_matched": total_matched,
        "replies_sent": total_replies,
        "snapshots_used": total_snapshots
    }


def show_stats():
    """显示今日统计"""
    config = load_config()
    stats = get_today_stats()

    print("\n" + "=" * 50)
    print("今日统计 (V3)")
    print("=" * 50)

    if not stats:
        print("  暂无今日数据")
        return

    daily_limit = config.get("global_settings", {}).get("daily_reply_limit", 30)
    remaining = max(0, daily_limit - stats["replies_sent"])
    replied_videos = len(get_replied_video_ids())

    print(f"  日期: {stats['date']}")
    print(f"  会话数: {len(stats['sessions'])}")
    print(f"  访问视频: {stats['videos_visited']}")
    print(f"  扫描评论: {stats['comments_scanned']}")
    print(f"  匹配评论: {stats['comments_matched']}")
    print(f"  已回复: {stats['replies_sent']} / {daily_limit}")
    print(f"  剩余额度: {remaining}")
    print(f"  已覆盖视频: {replied_videos} 个（去重）")
    print(f"  快照使用次数: {stats['snapshots_used']} (V3 目标: 0)")
    print()


def export_config_for_session():
    """导出当前配置为 session 可读格式（供 AI 使用）"""
    config = load_config()

    result = {
        "version": "3.0",
        "initialized": config.get("_initialized", False),
        "active_topics": [
            t for t in config["topics"] if t.get("enabled", True)
        ],
        "all_topics": config["topics"],
        "global": config.get("global_settings", {}),
        "today_stats": get_today_stats()
    }

    return result


def init_config():
    """初始化默认配置"""
    if CONFIG_FILE.exists():
        print("配置文件已存在")
        overwrite = input("  是否覆盖？(y/N): ").strip().lower()
        if overwrite != "y":
            print("  已取消")
            return

    save_config(DEFAULT_CONFIG)
    print("默认配置已创建")


# ─────────────────────────────────────────────
# 主入口
# ─────────────────────────────────────────────
if __name__ == "__main__":
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd == "init":
            init_config()
        elif cmd == "show":
            show_config()
        elif cmd == "stats":
            show_stats()
        elif cmd == "add-topic":
            add_topic_interactive()
        elif cmd == "export":
            output = sys.argv[2] if len(sys.argv) > 2 else None
            export_config(output)
        elif cmd == "import-config":
            if len(sys.argv) > 2:
                import_config(sys.argv[2])
            else:
                print("用法: python config_manager.py import-config <文件路径>")
        elif cmd == "templates":
            show_templates()
        elif cmd == "check":
            check_status()
        elif cmd == "export-session":
            data = export_config_for_session()
            print(json.dumps(data, ensure_ascii=False, indent=2))
        elif cmd == "history":
            days = int(sys.argv[2]) if len(sys.argv) > 2 else 7
            show_history(days)
        elif cmd == "replied":
            show_replied()
        elif cmd == "is-replied":
            if len(sys.argv) > 2:
                vid = sys.argv[2]
                print(f"视频 {vid} 已回复: {is_video_replied(vid)}")
            else:
                print("用法: python config_manager.py is-replied <video_id>")
        elif cmd == "clear-replied":
            confirm = input("确定清除所有已回复记录？(y/N): ").strip().lower()
            if confirm == "y":
                _save_replied({"replies": []})
                print("已清除所有已回复记录")
            else:
                print("已取消")
        else:
            print(f"未知命令: {cmd}")
            print("可用命令: init, show, stats, add-topic, templates, export, import-config,")
            print("          check, export-session, history [days], replied, is-replied <id>, clear-replied")
    else:
        # 交互模式
        print("抖音引流-psy V3 配置管理器")
        print("=" * 30)
        print("1. 查看配置")
        print("2. 添加话题")
        print("3. 查看今日统计")
        print("4. 查看行业模板")
        print("5. 导出配置")
        print("6. 导入配置")
        print("7. 初始化配置")
        print("8. 状态检查")
        print("9. 查看历史记录")
        print("10. 查看已回复记录")
        print("0. 退出")

        choice = input("\n请选择 (0-10): ").strip()
        if choice == "1":
            show_config()
        elif choice == "2":
            add_topic_interactive()
        elif choice == "3":
            show_stats()
        elif choice == "4":
            show_templates()
        elif choice == "5":
            export_config()
        elif choice == "6":
            path = input("配置文件路径: ").strip()
            import_config(path)
        elif choice == "7":
            init_config()
        elif choice == "8":
            check_status()
        elif choice == "9":
            days = int(input("查看最近几天？(默认7): ").strip() or "7")
            show_history(days)
        elif choice == "10":
            show_replied()
        else:
            print("再见")
