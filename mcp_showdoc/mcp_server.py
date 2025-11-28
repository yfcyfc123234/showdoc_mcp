from __future__ import annotations

import asyncio
import io
import logging
import sys
from typing import Optional, Annotated

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
    showdoc_fetch_apis,
    showdoc_fetch_node_tree,
    get_node_detail_info,
    get_node_cookie,
)

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

app = FastMCP("showdoc-mcp")


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
    output_dir: Annotated[Optional[str], "输出目录（默认 android_output）"] = None,
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
    - output_dir: 生成代码输出目录，例如 android_output
    - server_base: ShowDoc 服务器根地址，用于在注释中生成文档链接；默认从 base_url 推断
    - save_snapshot_path: 抓取结果快照保存路径（JSON 文件）
    - auto_delete_orphaned: 是否自动删除已孤立/待删除的旧文件（默认 False：只标记不删除）
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


