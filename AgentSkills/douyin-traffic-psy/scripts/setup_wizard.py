#!/usr/bin/env python3
"""
抖音引流-psy V3 — 一键环境诊断工具

用法：
  python setup_wizard.py          # 运行完整诊断
  python setup_wizard.py check    # 仅环境检测
  python setup_wizard.py mcp      # 显示 MCP 配置说明

此脚本用于检测运行环境是否满足要求，并输出诊断报告。
AI 在初始化引导时可以运行此脚本。
"""

import json
import os
import re
import subprocess
import sys
from pathlib import Path

# ─────────────────────────────────────────────
# 颜色输出
# ─────────────────────────────────────────────
class Color:
    OK = "\033[92m"
    FAIL = "\033[91m"
    WARN = "\033[93m"
    INFO = "\033[96m"
    END = "\033[0m"
    BOLD = "\033[1m"

def ok(msg):
    print(f"  {Color.OK}[PASS]{Color.END} {msg}")

def fail(msg):
    print(f"  {Color.FAIL}[FAIL]{Color.END} {msg}")

def warn(msg):
    print(f"  {Color.WARN}[WARN]{Color.END} {msg}")

def info(msg):
    print(f"  {Color.INFO}[INFO]{Color.END} {msg}")

def header(msg):
    print(f"\n{Color.BOLD}{'=' * 50}{Color.END}")
    print(f"{Color.BOLD}{msg}{Color.END}")
    print(f"{Color.BOLD}{'=' * 50}{Color.END}")


# ─────────────────────────────────────────────
# MCP 配置路径
# ─────────────────────────────────────────────
def get_mcp_path():
    """获取 MCP 配置文件路径"""
    home = Path.home()
    return home / ".workbuddy" / "mcp.json"


# ─────────────────────────────────────────────
# 环境检测
# ─────────────────────────────────────────────
def check_chrome_version():
    """检测 Chrome 版本"""
    try:
        # Windows: 从注册表或程序文件检测
        if sys.platform == "win32":
            # 尝试从常见路径获取 Chrome 版本
            chrome_paths = [
                r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
                os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
            ]
            for path in chrome_paths:
                if os.path.exists(path):
                    # 读取版本信息
                    version_dir = os.path.dirname(path)
                    # 尝试运行 chrome --version
                    try:
                        result = subprocess.run(
                            [path, "--version"],
                            capture_output=True, text=True, timeout=5
                        )
                        output = result.stdout.strip()
                        match = re.search(r"(\d+)\.", output)
                        if match:
                            version = int(match.group(1))
                            return version, output
                    except Exception:
                        pass

            # 备用：检查目录名中的版本号
            for base in [
                r"C:\Program Files\Google\Chrome\Application",
                r"C:\Program Files (x86)\Google\Chrome\Application",
            ]:
                if os.path.exists(base):
                    for item in os.listdir(base):
                        if re.match(r"\d+\.", item):
                            version = int(item.split(".")[0])
                            return version, f"Chrome {item}"

        # macOS / Linux
        elif sys.platform == "darwin":
            try:
                result = subprocess.run(
                    ["/Applications/Google Chrome.app/Contents/MacOS/Google Chrome", "--version"],
                    capture_output=True, text=True, timeout=5
                )
                match = re.search(r"(\d+)\.", result.stdout)
                if match:
                    return int(match.group(1)), result.stdout.strip()
            except Exception:
                pass
        else:
            try:
                result = subprocess.run(
                    ["google-chrome", "--version"],
                    capture_output=True, text=True, timeout=5
                )
                match = re.search(r"(\d+)\.", result.stdout)
                if match:
                    return int(match.group(1)), result.stdout.strip()
            except Exception:
                pass

        return None, "Chrome 未找到"
    except Exception as e:
        return None, f"检测失败: {e}"


def check_mcp_config():
    """检测 MCP 配置"""
    mcp_path = get_mcp_path()
    if not mcp_path.exists():
        return None, f"MCP 配置文件不存在: {mcp_path}"

    try:
        with open(mcp_path, "r", encoding="utf-8") as f:
            mcp_config = json.load(f)
    except json.JSONDecodeError:
        return None, f"MCP 配置文件 JSON 格式错误: {mcp_path}"

    servers = mcp_config.get("mcpServers", {})
    if "chrome-devtools" not in servers:
        return False, "chrome-devtools server 未配置"

    cd_config = servers["chrome-devtools"]
    args = cd_config.get("args", [])

    # 检查是否使用 --autoConnect
    has_auto_connect = "--autoConnect" in args
    # 也检查命令行参数（可能在 command 中）
    command = cd_config.get("command", "")
    if "--autoConnect" in command:
        has_auto_connect = True

    if not has_auto_connect:
        return False, "chrome-devtools 配置缺少 --autoConnect 参数"

    return True, f"chrome-devtools 已配置（--autoConnect 模式）"


def check_skill_config():
    """检测技能配置文件"""
    skill_dir = Path(__file__).parent.parent
    config_path = skill_dir / "config.json"

    if not config_path.exists():
        return None, "config.json 不存在"

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
    except json.JSONDecodeError:
        return None, "config.json 格式错误"

    topics = config.get("topics", [])
    initialized = config.get("_initialized", False)

    if not topics:
        return False, f"未配置话题（_initialized={initialized}），需要先运行初始化引导"

    active = [t for t in topics if t.get("enabled", True)]
    if not active:
        return False, f"有 {len(topics)} 个话题但全部已禁用"

    return True, f"已配置 {len(topics)} 个话题，{len(active)} 个已启用"


def check_node():
    """检测 Node.js"""
    try:
        result = subprocess.run(
            ["node", "--version"],
            capture_output=True, text=True, timeout=5
        )
        version = result.stdout.strip()
        if version:
            match = re.match(r"v(\d+)\.", version)
            major = int(match.group(1)) if match else 0
            if major >= 18:
                return True, f"Node.js {version}"
            else:
                return False, f"Node.js {version}（建议 >= 18）"
    except FileNotFoundError:
        pass
    return None, "Node.js 未安装"


def check_npx():
    """检测 npx"""
    try:
        result = subprocess.run(
            ["npx", "--version"],
            capture_output=True, text=True, timeout=5,
            shell=True
        )
        if result.stdout.strip():
            return True, f"npx {result.stdout.strip()}"
    except FileNotFoundError:
        pass
    except Exception:
        pass
    return None, "npx 不可用"


def check_data_dir():
    """检测数据目录"""
    skill_dir = Path(__file__).parent.parent
    data_dir = skill_dir / "data"

    if not data_dir.exists():
        try:
            data_dir.mkdir(parents=True, exist_ok=True)
            return True, f"数据目录已创建: {data_dir}"
        except Exception as e:
            return False, f"无法创建数据目录: {e}"

    return True, f"数据目录存在: {data_dir}"


# ─────────────────────────────────────────────
# 生成 MCP 配置说明
# ─────────────────────────────────────────────
def show_mcp_config():
    """显示 MCP 配置说明"""
    mcp_path = get_mcp_path()

    header("MCP 配置说明")

    print(f"\n配置文件路径: {mcp_path}")
    print(f"\n需要在 {mcp_path} 中添加以下配置：\n")

    mcp_example = {
        "mcpServers": {
            "chrome-devtools": {
                "command": "npx",
                "args": ["@anthropic-ai/mcp-server-chrome-devtools@latest", "--autoConnect"]
            }
        }
    }

    print(json.dumps(mcp_example, indent=2, ensure_ascii=False))
    print()

    if mcp_path.exists():
        with open(mcp_path, "r", encoding="utf-8") as f:
            existing = json.load(f)
        servers = existing.get("mcpServers", {})
        if "chrome-devtools" in servers:
            ok("chrome-devtools 已配置")
            print(f"  当前配置: {json.dumps(servers['chrome-devtools'], ensure_ascii=False)}")
        else:
            warn("chrome-devtools 未配置，请按上述说明添加")
    else:
        warn(f"mcp.json 不存在，请先创建: {mcp_path}")


# ─────────────────────────────────────────────
# 完整诊断
# ─────────────────────────────────────────────
def run_full_check():
    """运行完整环境诊断"""
    header("抖音引流-psy V3 环境诊断")

    results = []

    # 1. Chrome 版本
    print("\n[1] Chrome 浏览器")
    version, msg = check_chrome_version()
    if version is None:
        fail(msg)
        info("请安装 Chrome >= 144: https://www.google.com/chrome/")
        results.append(False)
    elif version >= 144:
        ok(f"Chrome {version}（满足 >= 144 要求）")
        results.append(True)
    else:
        fail(f"Chrome {version}（需要 >= 144，当前版本过低）")
        info("请更新 Chrome: https://www.google.com/chrome/")
        results.append(False)

    # 2. MCP 配置
    print("\n[2] MCP 配置（chrome-devtools）")
    status, msg = check_mcp_config()
    if status is True:
        ok(msg)
        results.append(True)
    elif status is False:
        fail(msg)
        show_mcp_config()
        results.append(False)
    else:
        fail(msg)
        show_mcp_config()
        results.append(False)

    # 3. 技能配置
    print("\n[3] 技能配置")
    status, msg = check_skill_config()
    if status is True:
        ok(msg)
        results.append(True)
    elif status is False:
        warn(msg)
        info("请通过 AI 对话完成配置（对 AI 说「帮我设置抖音引流」）")
        results.append(False)  # 不是硬性失败
    else:
        fail(msg)
        results.append(False)

    # 4. Node.js
    print("\n[4] Node.js")
    status, msg = check_node()
    if status is True:
        ok(msg)
        results.append(True)
    elif status is False:
        warn(msg)
        results.append(False)
    else:
        fail(msg)
        info("请安装 Node.js >= 18: https://nodejs.org/")
        results.append(False)

    # 5. npx
    print("\n[5] npx")
    status, msg = check_npx()
    if status is True:
        ok(msg)
        results.append(True)
    elif status is False:
        warn(msg)
        results.append(False)
    else:
        fail(msg)
        results.append(False)

    # 6. 数据目录
    print("\n[6] 数据目录")
    status, msg = check_data_dir()
    if status:
        ok(msg)
        results.append(True)
    else:
        fail(msg)
        results.append(False)

    # 总结
    passed = sum(results)
    total = len(results)
    hard_required = results[:2] + results[3:]  # 除技能配置外的所有检测
    hard_passed = sum(hard_required)

    header("诊断结果")

    if hard_passed == len(hard_required) and results[2]:
        print(f"\n{Color.OK}{Color.BOLD}所有检测通过！环境就绪。{Color.END}")
        print(f"\n下一步：")
        print(f"  1. 确保 Chrome 已开启远程调试：访问 chrome://inspect/#remote-debugging")
        print(f"  2. 确保 Chrome 已登录抖音账号")
        print(f"  3. 对 AI 说「开始抖音引流」即可运行")
    elif hard_passed == len(hard_required):
        print(f"\n{Color.WARN}{Color.BOLD}环境就绪，但需要配置话题{Color.END}")
        print(f"\n请对 AI 说「帮我设置抖音引流」，AI 会引导你完成配置")
    else:
        hard_failed = len(hard_required) - hard_passed
        print(f"\n{Color.FAIL}{Color.BOLD}环境未就绪，{hard_passed}/{len(hard_required)} 项通过，{hard_failed} 项未满足{Color.END}")
        print(f"\n请按上述说明逐项修复，然后重新运行: python setup_wizard.py check")

    print()
    return all(results)


# ─────────────────────────────────────────────
# 主入口
# ─────────────────────────────────────────────
if __name__ == "__main__":
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd == "check":
            run_full_check()
        elif cmd == "mcp":
            show_mcp_config()
        elif cmd == "templates":
            from config_manager import show_templates
            show_templates()
        elif cmd == "export":
            from config_manager import export_config
            export_config()
        else:
            print(f"未知命令: {cmd}")
            print("可用命令: (无参数=完整诊断), check, mcp, templates, export")
    else:
        run_full_check()
