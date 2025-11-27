from __future__ import annotations

import asyncio
import io
import logging
import sys
from typing import Optional

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

app = FastMCP("showdoc-android-mcp")


@app.tool()
async def fetch_showdoc_apis(
    base_url: str,
    cookie: Optional[str] = None,
    password: Optional[str] = "123456",
    node_name: Optional[str] = None,
    save_path: Optional[str] = None,
) -> dict:
    """
    从 ShowDoc 抓取接口树，并可选保存为本地快照。

    必需参数：
    - base_url: ShowDoc 项目 URL，例如 https://doc.cqfengli.com/web/#/90/

    认证参数（二选一）：
    - cookie: 浏览器里的 Cookie，用于鉴权
    - password: 项目访问密码（默认: "123456"），将自动进行验证码登录

    可选参数：
    - node_name: 节点（分类）名称；None / "全部" / "all" 表示全量抓取
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
async def generate_android_from_showdoc(
    base_url: str,
    cookie: Optional[str] = None,
    password: Optional[str] = "123456",
    node_name: Optional[str] = None,
    base_package: str = "com.example.api",
    output_dir: Optional[str] = None,
    server_base: Optional[str] = None,
    save_snapshot_path: Optional[str] = None,
    auto_delete_orphaned: bool = False,
) -> dict:
    """
    一键从 ShowDoc 抓取接口树并生成 Android 代码。

    必需参数：
    - base_url: ShowDoc 项目 URL，例如 https://doc.cqfengli.com/web/#/90/

    认证参数（二选一）：
    - cookie: 浏览器里的 Cookie，用于鉴权
    - password: 项目访问密码（默认: "123456"），将自动进行验证码登录

    可选参数：
    - node_name: 只生成指定节点（分类）下的接口；None 表示全部
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


def main() -> None:
    """MCP stdio 入口。"""
    app.run()


if __name__ == "__main__":
    main()


