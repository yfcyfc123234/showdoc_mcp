from __future__ import annotations

import asyncio
import io
import logging
import sys
from typing import Optional, Annotated, List, Dict, Any

try:
    from mcp.server.fastmcp import FastMCP, ToolError
except ImportError:
    # 兼容旧版本 fastmcp：只有 FastMCP，没有 ToolError
    from mcp.server.fastmcp import FastMCP

    class ToolError(RuntimeError):
        """Fallback ToolError for旧版本 MCP。"""
        pass

from .server import (
    showdoc_fetch_and_generate,
    showdoc_fetch_and_generate_flutter,
    showdoc_fetch_apis,
    showdoc_fetch_node_tree,
    get_node_detail_info,
    get_node_cookie,
)
from cursor_agents import CursorAgentsClient

# 配置日志到 UTF-8 stderr，避免干扰 MCP 协议的 stdout
utf8_stderr = io.TextIOWrapper(
    sys.stderr.buffer, encoding="utf-8", errors="replace", line_buffering=True
)

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    stream=utf8_stderr,
    force=True,
)

app = FastMCP("personal-mcp")


@app.tool()
async def fetch_showdoc_apis(
    base_url: Annotated[str, "ShowDoc 项目 URL，可使用 web/#/ 或分享链接"],
    cookie: Annotated[Optional[str], "可选，浏览器复制的 Cookie"] = None,
    password: Annotated[Optional[str], "可选，项目访问密码（默认 123456）"] = "123456",
    node_name: Annotated[Optional[str], "可选，只抓取该分类及子节点"] = None,
    save_path: Annotated[Optional[str], "可选，抓取结果保存到本地 JSON"] = None,
) -> dict:
    """
    从 ShowDoc 抓取接口树，并可选保存为本地快照。

    必需参数：
    - base_url: ShowDoc 项目 URL，例如 https://doc.cqfengli.com/web/#/90/

    认证参数（二选一）：
    - cookie: 浏览器里的 Cookie，用于鉴权
    - password: 项目访问密码（默认: "123456"），将自动进行验证码登录

    可选参数：
    - node_name: 节点（分类）名称；None / "全部" / "all" 表示全量抓取；如果 base_url 包含页面 ID（如 /94/4828），且 node_name 为空，则自动抓取该页面所在的节点
    - save_path: 抓取结果快照保存路径（JSON 文件），不填则只返回内存结果
    """
    if not base_url:
        raise ToolError("base_url 参数是必需的")
    if not cookie and not password:
        raise ToolError("必须提供 cookie 或 password 之一进行认证")

    result = await asyncio.to_thread(
        showdoc_fetch_apis,
        base_url=base_url,
        cookie=cookie,
        password=password,
        node_name=node_name,
        save_path=save_path,
    )

    if not result.get("ok"):
        raise ToolError(result.get("error") or "抓取失败")

    return result


@app.tool()
async def fetch_showdoc_node_tree(
    base_url: Annotated[str, "ShowDoc 项目 URL（支持分享链接）"],
    cookie: Annotated[Optional[str], "可选，已有 Cookie，跳过验证码"] = None,
    password: Annotated[Optional[str], "可选，项目访问密码（默认 123456）"] = "123456",
    node_name: Annotated[Optional[str], "可选，只返回某个节点的子树；如果 base_url 包含页面 ID 且 node_name 为空，则自动返回该页面所在的节点"] = None,
) -> dict:
    """
    抓取轻量级的节点树（只包含分类与页面名称），每个节点包含跳转链接。
    
    如果 base_url 包含页面 ID（如 https://doc.cqfengli.com/web/#/94/4828），
    且 node_name 为空，则自动返回该页面所在的节点。
    """
    if not base_url:
        raise ToolError("base_url 参数是必需的")
    if not cookie and not password:
        raise ToolError("必须提供 cookie 或 password 之一进行认证")

    result = await asyncio.to_thread(
        showdoc_fetch_node_tree,
        base_url=base_url,
        cookie=cookie,
        password=password,
        node_name=node_name,
    )

    if not result.get("ok"):
        raise ToolError(result.get("error") or "节点树抓取失败")

    return result


@app.tool()
async def generate_android_from_showdoc(
    base_url: Annotated[str, "ShowDoc 项目 URL"],
    cookie: Annotated[Optional[str], "可选，浏览器 Cookie"] = None,
    password: Annotated[Optional[str], "可选，项目访问密码（默认 123456）"] = "123456",
    node_name: Annotated[Optional[str], "可选，只生成指定分类；如果 base_url 包含页面 ID 且 node_name 为空，则自动生成该页面所在的节点"] = None,
    base_package: Annotated[str, "生成代码使用的 Kotlin 包名"] = "com.example.api",
    output_dir: Annotated[Optional[str], "输出目录（相对路径，相对于当前项目根目录）。默认：output/android_output，代码将保存在当前项目目录下的 output/android_output/ 文件夹中"] = None,
    server_base: Annotated[Optional[str], "可选，生成注释用的文档域名"] = None,
    save_snapshot_path: Annotated[Optional[str], "可选，抓取结果保存路径"] = None,
    auto_delete_orphaned: Annotated[bool, "是否自动删除已孤立文件"] = False,
) -> dict:
    """
    一键从 ShowDoc 抓取接口树并生成 Android 代码。

    必需参数：
    - base_url: ShowDoc 项目 URL，例如 https://doc.cqfengli.com/web/#/90/

    认证参数（二选一）：
    - cookie: 浏览器里的 Cookie，用于鉴权
    - password: 项目访问密码（默认: "123456"），将自动进行验证码登录

    可选参数：
    - node_name: 只生成指定节点（分类）下的接口；None 表示全部；如果 base_url 包含页面 ID（如 /94/4828），且 node_name 为空，则自动生成该页面所在的节点
    - base_package: Kotlin 包名，例如 com.example.api
    - output_dir: 生成代码输出目录（相对路径，相对于当前项目根目录）。默认：output/android_output，代码将保存在当前项目目录下的 output/android_output/ 文件夹中。如果指定相对路径，将相对于当前项目根目录解析。
    - server_base: ShowDoc 服务器根地址，用于在注释中生成文档链接；默认从 base_url 推断
    - save_snapshot_path: 抓取结果快照保存路径（JSON 文件）
    - auto_delete_orphaned: 是否自动删除已孤立/待删除的旧文件（默认 False：只标记不删除）

    注意：生成的代码默认保存在当前项目根目录下的 output/android_output/ 文件夹中。
    """
    if not base_url:
        raise ToolError("base_url 参数是必需的")
    if not cookie and not password:
        raise ToolError("必须提供 cookie 或 password 之一进行认证")

    result = await asyncio.to_thread(
        showdoc_fetch_and_generate,
        base_url=base_url,
        cookie=cookie,
        password=password,
        node_name=node_name,
        base_package=base_package,
        output_dir=output_dir,
        server_base=server_base,
        save_snapshot_path=save_snapshot_path,
        auto_delete_orphaned=auto_delete_orphaned,
    )

    if not result.get("ok"):
        raise ToolError(result.get("error") or "生成失败")

    return result


@app.tool()
async def fetch_node_detail_info(
    base_url: Annotated[str, "ShowDoc 项目 URL"],
    node_name: Annotated[Optional[str], "可选，节点名称（分类名称）"] = None,
    page_id: Annotated[Optional[str], "可选，页面 ID（如果URL中包含会自动提取）"] = None,
    cookie: Annotated[Optional[str], "可选，认证 Cookie"] = None,
    password: Annotated[Optional[str], "可选，项目访问密码（默认 123456）"] = "123456",
    snapshot_path: Annotated[Optional[str], "可选，本地快照文件路径，如果为None则自动查找最新的快照"] = None,
) -> dict:
    """
    查询指定节点（或URL）的详细信息。
    
    逻辑：
    1. 如果本地有缓存（snapshot_path 或自动查找），优先使用缓存数据
    2. 如果没有缓存，重新抓取数据
    3. 如果节点信息不是API的（api_info为null），调用 /api/page/info 接口获取详细信息
    
    必需参数：
    - base_url: ShowDoc 项目 URL，例如 https://doc.cqfengli.com/web/#/90/
    
    可选参数：
    - node_name: 节点名称（分类名称）
    - page_id: 页面 ID（如果URL中包含会自动提取）
    - cookie: 认证 Cookie
    - password: 项目访问密码（默认: "123456"）
    - snapshot_path: 本地快照文件路径，如果为None则自动查找最新的快照
    """
    if not base_url:
        raise ToolError("base_url 参数是必需的")
    
    result = await asyncio.to_thread(
        get_node_detail_info,
        base_url=base_url,
        node_name=node_name,
        page_id=page_id,
        cookie=cookie,
        password=password,
        snapshot_path=snapshot_path,
    )
    
    if not result.get("ok"):
        raise ToolError(result.get("error") or "查询节点详细信息失败")
    
    return result


@app.tool()
async def fetch_node_cookie(
    base_url: Annotated[str, "ShowDoc 项目 URL"],
    cookie: Annotated[Optional[str], "可选，认证 Cookie（如果提供则直接使用并保存）"] = None,
    password: Annotated[Optional[str], "可选，项目访问密码（默认 123456）"] = "123456",
) -> dict:
    """
    查询指定节点所需的已登录的cookie信息。
    
    逻辑：
    1. 优先从本地缓存文件（output/.showdoc_cookies.json）读取
    2. 如果没有缓存或已过期，重新走登录逻辑生成并获取
    
    必需参数：
    - base_url: ShowDoc 项目 URL，例如 https://doc.cqfengli.com/web/#/90/
    
    可选参数：
    - cookie: 认证 Cookie（如果提供则直接使用并保存）
    - password: 项目访问密码（默认: "123456"）
    """
    if not base_url:
        raise ToolError("base_url 参数是必需的")
    
    result = await asyncio.to_thread(
        get_node_cookie,
        base_url=base_url,
        cookie=cookie,
        password=password,
    )
    
    if not result.get("ok"):
        raise ToolError(result.get("error") or "获取Cookie失败")
    
    return result


@app.tool()
async def generate_flutter_from_showdoc(
    base_url: Annotated[str, "ShowDoc 项目 URL"],
    cookie: Annotated[Optional[str], "可选，浏览器 Cookie"] = None,
    password: Annotated[Optional[str], "可选，项目访问密码（默认 123456）"] = "123456",
    node_name: Annotated[Optional[str], "可选，只生成指定分类；如果 base_url 包含页面 ID 且 node_name 为空，则自动生成该页面所在的节点"] = None,
    base_package: Annotated[str, "生成代码使用的 Dart 包名"] = "com.example.api",
    output_dir: Annotated[Optional[str], "输出目录（相对路径，相对于当前项目根目录）。默认：output/flutter_output，代码将保存在当前项目目录下的 output/flutter_output/ 文件夹中"] = None,
    server_base: Annotated[Optional[str], "可选，生成注释用的文档域名"] = None,
    save_snapshot_path: Annotated[Optional[str], "可选，抓取结果保存路径"] = None,
    auto_delete_orphaned: Annotated[bool, "是否自动删除已孤立文件"] = False,
) -> dict:
    """
    一键从 ShowDoc 抓取接口树并生成 Flutter 代码。

    必需参数：
    - base_url: ShowDoc 项目 URL，例如 https://doc.cqfengli.com/web/#/90/

    认证参数（二选一）：
    - cookie: 浏览器里的 Cookie，用于鉴权
    - password: 项目访问密码（默认: "123456"），将自动进行验证码登录

    可选参数：
    - node_name: 只生成指定节点（分类）下的接口；None 表示全部；如果 base_url 包含页面 ID（如 /94/4828），且 node_name 为空，则自动生成该页面所在的节点
    - base_package: Dart 包名，例如 com.example.api
    - output_dir: 生成代码输出目录（相对路径，相对于当前项目根目录）。默认：output/flutter_output，代码将保存在当前项目目录下的 output/flutter_output/ 文件夹中。如果指定相对路径，将相对于当前项目根目录解析。
    - server_base: ShowDoc 服务器根地址，用于在注释中生成文档链接；默认从 base_url 推断
    - save_snapshot_path: 抓取结果快照保存路径（JSON 文件）
    - auto_delete_orphaned: 是否自动删除已孤立/待删除的旧文件（默认 False：只标记不删除）

    注意：生成的代码默认保存在当前项目根目录下的 output/flutter_output/ 文件夹中。
    """
    if not base_url:
        raise ToolError("base_url 参数是必需的")
    if not cookie and not password:
        raise ToolError("必须提供 cookie 或 password 之一进行认证")

    result = await asyncio.to_thread(
        showdoc_fetch_and_generate_flutter,
        base_url=base_url,
        cookie=cookie,
        password=password,
        node_name=node_name,
        base_package=base_package,
        output_dir=output_dir,
        server_base=server_base,
        save_snapshot_path=save_snapshot_path,
        auto_delete_orphaned=auto_delete_orphaned,
    )

    if not result.get("ok"):
        raise ToolError(result.get("error") or "生成失败")

    return result


# ========== Cursor Cloud Agents API 工具 ==========

@app.tool()
async def set_cursor_api_key_tool(
    api_key: Annotated[str, "Cursor API 密钥，从 https://cursor.com/settings 获取"],
    fetch_user_info: Annotated[bool, "是否获取并缓存用户信息（默认 True，首次设置时建议为 True）"] = True,
) -> dict:
    """
    设置并缓存 Cursor Cloud Agents API 密钥。
    
    首次设置时会自动调用 /v0/me API 获取用户信息（API Key 名称、创建时间、用户邮箱等），
    并缓存到 output/.cursor_api_key_info.json 供以后使用。
    
    必需参数：
    - api_key: 从 Cursor 仪表盘 (https://cursor.com/settings) 获取的 API 密钥
    
    可选参数：
    - fetch_user_info: 是否获取用户信息（默认 True）
    
    设置后，后续调用其他 Cursor Agents 工具时，如果不提供 api_key 参数，将自动使用缓存的密钥。
    """
    try:
        client = CursorAgentsClient()
        result = await asyncio.to_thread(client.set_api_key, api_key, fetch_user_info)
        return result
    except Exception as e:
        raise ToolError(f"设置 API Key 失败: {e}")


@app.tool()
async def list_cursor_agents_tool(
    limit: Annotated[int, "返回的云端代理数量（默认 20，最大 100）"] = 20,
    cursor: Annotated[Optional[str], "分页游标"] = None,
    api_key: Annotated[Optional[str], "可选，临时指定 API Key（不缓存）"] = None,
) -> dict:
    """
    列出当前已认证用户的所有云端代理。
    
    可选参数：
    - limit: 返回的云端代理数量（默认 20，最大 100）
    - cursor: 上一页响应中的分页游标
    - api_key: 临时指定 API Key（如果提供，不会缓存；如果不提供，使用缓存的密钥）
    """
    try:
        client = CursorAgentsClient(api_key=api_key)
        result = await asyncio.to_thread(client.list_agents, limit=limit, cursor=cursor)
        return {
            "ok": True,
            **result
        }
    except Exception as e:
        raise ToolError(f"列出代理失败: {e}")


@app.tool()
async def get_cursor_agent_status_tool(
    agent_id: Annotated[str, "云端 Agent 的唯一标识符（例如：bc_abc123）"],
    api_key: Annotated[Optional[str], "可选，临时指定 API Key（不缓存）"] = None,
) -> dict:
    """
    获取云端 Agent 的当前状态和结果。
    
    必需参数：
    - agent_id: 云端 Agent 的唯一标识符（例如：bc_abc123）
    
    可选参数：
    - api_key: 临时指定 API Key（如果提供，不会缓存；如果不提供，使用缓存的密钥）
    """
    try:
        client = CursorAgentsClient(api_key=api_key)
        result = await asyncio.to_thread(client.get_agent_status, agent_id=agent_id)
        return {
            "ok": True,
            **result
        }
    except Exception as e:
        raise ToolError(f"获取 Agent 状态失败: {e}")


@app.tool()
async def get_cursor_agent_conversation_tool(
    agent_id: Annotated[str, "云端 Agent 的唯一标识符（例如：bc_abc123）"],
    api_key: Annotated[Optional[str], "可选，临时指定 API Key（不缓存）"] = None,
) -> dict:
    """
    获取云端 Agent 的会话历史，包括所有用户提问与助手回复。
    
    注意：如果云端 Agent 已被删除，将无法访问该会话。
    
    必需参数：
    - agent_id: 云端 Agent 的唯一标识符（例如：bc_abc123）
    
    可选参数：
    - api_key: 临时指定 API Key（如果提供，不会缓存；如果不提供，使用缓存的密钥）
    """
    try:
        client = CursorAgentsClient(api_key=api_key)
        result = await asyncio.to_thread(client.get_agent_conversation, agent_id=agent_id)
        return {
            "ok": True,
            **result
        }
    except Exception as e:
        raise ToolError(f"获取 Agent 会话失败: {e}")


@app.tool()
async def add_cursor_agent_followup_tool(
    agent_id: Annotated[str, "云代理的唯一标识符（例如：bc_abc123）"],
    text: Annotated[str, "给代理的后续指令文本"],
    images: Annotated[Optional[List[Dict[str, Any]]], "可选，包含 base64 数据与尺寸的图片对象数组（最多 5 个）"] = None,
    api_key: Annotated[Optional[str], "可选，临时指定 API Key（不缓存）"] = None,
) -> dict:
    """
    为现有云代理添加后续指令。
    
    必需参数：
    - agent_id: 云代理的唯一标识符（例如：bc_abc123）
    - text: 给代理的后续指令文本
    
    可选参数：
    - images: 图片对象数组（最多 5 个），每个对象应包含：
      - data: base64 编码的图片数据
      - dimension: 包含 width 和 height 的字典
    - api_key: 临时指定 API Key（如果提供，不会缓存；如果不提供，使用缓存的密钥）
    """
    try:
        client = CursorAgentsClient(api_key=api_key)
        result = await asyncio.to_thread(
            client.add_followup,
            agent_id=agent_id,
            text=text,
            images=images
        )
        return {
            "ok": True,
            **result
        }
    except Exception as e:
        raise ToolError(f"添加跟进失败: {e}")


@app.tool()
async def delete_cursor_agent_tool(
    agent_id: Annotated[str, "云代理的唯一标识符（例如：bc_abc123）"],
    api_key: Annotated[Optional[str], "可选，临时指定 API Key（不缓存）"] = None,
) -> dict:
    """
    删除云代理。此操作永久生效且不可撤销。
    
    必需参数：
    - agent_id: 云代理的唯一标识符（例如：bc_abc123）
    
    可选参数：
    - api_key: 临时指定 API Key（如果提供，不会缓存；如果不提供，使用缓存的密钥）
    """
    try:
        client = CursorAgentsClient(api_key=api_key)
        result = await asyncio.to_thread(client.delete_agent, agent_id=agent_id)
        return {
            "ok": True,
            **result
        }
    except Exception as e:
        raise ToolError(f"删除代理失败: {e}")


@app.tool()
async def get_cursor_api_key_info_tool(
    api_key: Annotated[Optional[str], "可选，临时指定 API Key（不缓存）"] = None,
) -> dict:
    """
    获取用于身份验证的 API 密钥相关信息。
    
    可选参数：
    - api_key: 临时指定 API Key（如果提供，不会缓存；如果不提供，使用缓存的密钥）
    """
    try:
        client = CursorAgentsClient(api_key=api_key)
        result = await asyncio.to_thread(client.get_api_key_info)
        return {
            "ok": True,
            **result
        }
    except Exception as e:
        raise ToolError(f"获取 API Key 信息失败: {e}")


@app.tool()
async def list_cursor_models_tool(
    api_key: Annotated[Optional[str], "可选，临时指定 API Key（不缓存）"] = None,
) -> dict:
    """
    获取云端代理的推荐模型列表。
    
    注意：建议提供"Auto"选项，当创建端点不提供模型名称时，会自动选择最合适的模型。
    
    可选参数：
    - api_key: 临时指定 API Key（如果提供，不会缓存；如果不提供，使用缓存的密钥）
    """
    try:
        client = CursorAgentsClient(api_key=api_key)
        result = await asyncio.to_thread(client.list_models)
        return {
            "ok": True,
            **result
        }
    except Exception as e:
        raise ToolError(f"列出模型失败: {e}")


@app.tool()
async def list_cursor_repositories_tool(
    api_key: Annotated[Optional[str], "可选，临时指定 API Key（不缓存）"] = None,
) -> dict:
    """
    获取已认证用户可访问的 GitHub 仓库列表。
    
    警告：此端点有非常严格的速率限制（1 次/用户/分钟，30 次/用户/小时）。
    对于可访问大量仓库的用户，此请求可能需要数十秒才会返回。
    请确保在该信息不可用时进行优雅降级处理。
    
    可选参数：
    - api_key: 临时指定 API Key（如果提供，不会缓存；如果不提供，使用缓存的密钥）
    """
    try:
        client = CursorAgentsClient(api_key=api_key)
        result = await asyncio.to_thread(client.list_repositories)
        return {
            "ok": True,
            **result
        }
    except Exception as e:
        raise ToolError(f"列出仓库失败: {e}")


def main() -> None:
    """MCP stdio 入口。"""
    # 检查是否有测试参数
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        print("MCP 服务器测试模式：服务器已就绪，等待 MCP 客户端连接...", file=sys.stderr)
        print("提示：这是正常的，MCP 服务器通过 stdin/stdout 与客户端通信。", file=sys.stderr)
        print("要使用服务器，请在 Cursor 中配置 MCP 服务器。", file=sys.stderr)
        print("按 Ctrl+C 退出测试模式。", file=sys.stderr)
    
    # 启动 MCP 服务器（会阻塞等待 stdin 输入）
    app.run()


if __name__ == "__main__":
    main()


