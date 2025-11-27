"""
MCP 服务器：ShowDoc → Android 代码生成

提供三个工具（函数）：
- showdoc_fetch_apis: 从 ShowDoc 抓取接口定义，并可选保存为本地快照；
- android_generate_from_showdoc: 基于抓取结果（JSON 或快照文件）生成 Android 代码；
- android_open_output_folder: 返回 / 打开当前 Android 输出目录。

说明：
- 这里不绑定具体 MCP 传输实现（stdin/stdout、HTTP 等），只提供「纯 Python 函数」，
  上层可以按需适配到具体的 MCP Server 框架。
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, Optional, Callable, List

from core import ShowDocClient, ShowDocNotFoundError, ShowDocAuthError, ShowDocNetworkError
from core.models import ApiTree, ItemInfo, Category, Page, ApiDefinition
from android_codegen import AndroidCodeGenerator


# ========== 通用配置 ==========

DEFAULT_OUTPUT_DIR = "android_output"


# ========== 辅助方法 ==========

def _api_tree_from_dict(data: Dict[str, Any]) -> ApiTree:
    """
    将 ApiTree.to_dict() 的结果反向还原为 ApiTree 对象。

    说明：
    - 这里只恢复代码生成所需的核心字段（item_id、item_name、分类、页面、api 基本信息）；
    - 更细节的字段如果后续需要，可以再按需扩展。
    """

    item_info_raw = data.get("item_info") or {}
    item_info = ItemInfo(
        item_id=str(item_info_raw.get("item_id", "")),
        item_name=item_info_raw.get("item_name", ""),
        item_domain="",
        is_archived="0",
    )

    def category_from_dict(cat_dict: Dict[str, Any]) -> Category:
        pages: list[Page] = []
        for page_dict in cat_dict.get("pages", []) or []:
            api_info_raw = page_dict.get("api_info")
            api_info: Optional[ApiDefinition] = None
            if api_info_raw:
                api_info = ApiDefinition(
                    method=api_info_raw.get("method", "GET"),
                    url=api_info_raw.get("url", ""),
                    title=api_info_raw.get("title", ""),
                    description=api_info_raw.get("description", ""),
                    request=api_info_raw.get("request"),
                    response=api_info_raw.get("response"),
                )

            page = Page(
                page_id=str(page_dict.get("page_id", "")),
                page_title=page_dict.get("page_title", ""),
                cat_id=str(cat_dict.get("cat_id", "")),
                api_info=api_info,
            )
            pages.append(page)

        children_dicts = cat_dict.get("children") or []
        children = [category_from_dict(child) for child in children_dicts]

        return Category(
            cat_id=str(cat_dict.get("cat_id", "")),
            cat_name=cat_dict.get("cat_name", ""),
            item_id=item_info.item_id,
            parent_cat_id=str(cat_dict.get("parent_cat_id", "")),
            level=int(cat_dict.get("level", 0)),
            s_number=str(cat_dict.get("s_number", "")),
            pages=pages,
            children=children,
        )

    categories = [category_from_dict(c) for c in data.get("categories") or []]
    return ApiTree(item_info=item_info, categories=categories)


def _normalize_output_dir(output_dir: Optional[str]) -> Path:
    """统一处理输出目录，None 时使用默认目录。"""
    if not output_dir:
        output_dir = DEFAULT_OUTPUT_DIR
    return Path(output_dir).resolve()


def _extract_server_base(base_url: str) -> Optional[str]:
    """从完整的 ShowDoc base_url 中提取 server_base（协议 + 域名）。"""
    try:
        from urllib.parse import urlparse

        parsed = urlparse(base_url)
        if not parsed.scheme or not parsed.netloc:
            return None
        return f"{parsed.scheme}://{parsed.netloc}"
    except Exception:
        return None


# ========== MCP 工具 1：ShowDoc 抓取 ==========

def showdoc_fetch_apis(
    base_url: str,
    cookie: Optional[str] = None,
    password: Optional[str] = "123456",
    node_name: Optional[str] = None,
    save_path: Optional[str] = None,
) -> Dict[str, Any]:
    """
    从 ShowDoc 抓取接口树。

    Args:
        base_url: ShowDoc 项目 URL，例如 "https://doc.cqfengli.com/web/#/90/"
        cookie: 认证 Cookie（可选，如果提供 password 则可不提供）
        password: 项目访问密码（默认: "123456"），如果提供 cookie 则可不提供，将自动进行验证码登录
        node_name: 可选节点名称（分类），None/"全部"/"all" 表示全量
        save_path: 可选，本地快照保存路径（JSON），如 "showdoc_export_90.json"

    Returns:
        {
            "ok": bool,
            "error": Optional[str],
            "api_tree": Optional[dict],
            "snapshot_path": Optional[str],
        }
    """
    try:
        client = ShowDocClient(base_url, cookie=cookie, password=password)
        api_tree = client.get_all_apis(node_name=node_name)
        api_tree_dict = api_tree.to_dict()

        snapshot_path: Optional[str] = None
        if save_path:
            snapshot_file = Path(save_path).resolve()
            snapshot_file.parent.mkdir(parents=True, exist_ok=True)
            snapshot_file.write_text(
                json.dumps(api_tree_dict, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            snapshot_path = str(snapshot_file)

        return {
            "ok": True,
            "error": None,
            "api_tree": api_tree_dict,
            "snapshot_path": snapshot_path,
        }
    except ShowDocAuthError as e:
        return {"ok": False, "error": f"auth_error: {e}", "api_tree": None, "snapshot_path": None}
    except ShowDocNotFoundError as e:
        return {"ok": False, "error": f"not_found: {e}", "api_tree": None, "snapshot_path": None}
    except ShowDocNetworkError as e:
        return {"ok": False, "error": f"network_error: {e}", "api_tree": None, "snapshot_path": None}
    except Exception as e:
        return {"ok": False, "error": f"unknown_error: {e}", "api_tree": None, "snapshot_path": None}


# ========== MCP 工具 2：Android 代码生成 ==========

def android_generate_from_showdoc(
    api_tree_json: Optional[Dict[str, Any]] = None,
    snapshot_path: Optional[str] = None,
    base_package: str = "com.example.api",
    output_dir: Optional[str] = None,
    category_filter: Optional[str] = None,
    server_base: Optional[str] = None,
    auto_delete_orphaned: bool = False,
) -> Dict[str, Any]:
    """
    基于 ShowDoc 抓取结果生成 Android 代码。

    支持两种输入模式：
    - 直接传入 api_tree_json（优先级更高）；
    - 或传入 snapshot_path，从本地 JSON 文件读取。
    """
    if api_tree_json is None and not snapshot_path:
        return {
            "ok": False,
            "error": "invalid_args: api_tree_json 和 snapshot_path 至少需要提供一个",
        }

    try:
        data: Dict[str, Any]
        if api_tree_json is not None:
            data = api_tree_json
        else:
            snapshot_file = Path(snapshot_path).resolve()
            if not snapshot_file.exists():
                return {
                    "ok": False,
                    "error": f"snapshot_not_found: {snapshot_file}",
                }
            content = snapshot_file.read_text(encoding="utf-8")
            data = json.loads(content)

        api_tree = _api_tree_from_dict(data)

        out_dir = _normalize_output_dir(output_dir)
        generator = AndroidCodeGenerator(base_package=base_package, output_dir=str(out_dir))

        # 如果 server_base 未显式提供，可以尝试从 item_domain 或 snapshot_path 推断（这里保持简单）
        generated = generator.generate(
            api_tree,
            category_filter=category_filter,
            server_base=server_base,
            auto_delete_orphaned=auto_delete_orphaned,
        )

        return {
            "ok": True,
            "error": None,
            "output_dir": str(out_dir),
            "generated": generated,
        }
    except Exception as e:
        return {
            "ok": False,
            "error": f"generate_failed: {e}",
        }


# ========== MCP 工具 3：打开 / 返回输出目录 ==========

def android_open_output_folder(
    output_dir: Optional[str] = None,
    open_in_explorer: bool = False,
) -> Dict[str, Any]:
    """
    返回（可选：尝试在本机文件管理器中打开）当前 Android 输出目录。
    """
    out_dir = _normalize_output_dir(output_dir)
    exists = out_dir.exists()

    opened = False
    open_error: Optional[str] = None

    if open_in_explorer:
        try:
            if os.name == "nt":
                # Windows 使用 explorer 打开
                os.startfile(str(out_dir))  # type: ignore[attr-defined]
            elif sys.platform == "darwin":
                import subprocess

                subprocess.Popen(["open", str(out_dir)])
            else:
                import subprocess

                subprocess.Popen(["xdg-open", str(out_dir)])
            opened = True
        except Exception as e:
            open_error = str(e)

    return {
        "ok": True,
        "output_dir": str(out_dir),
        "exists": exists,
        "opened": opened,
        "open_error": open_error,
    }


__all__ = [
    "showdoc_fetch_apis",
    "android_generate_from_showdoc",
    "android_open_output_folder",
]


# ========== 组合工具：一键抓取 + 生成 ==========

def showdoc_fetch_and_generate(
    base_url: str,
    cookie: Optional[str] = None,
    password: Optional[str] = "123456",
    node_name: Optional[str] = None,
    base_package: str = "com.example.api",
    output_dir: Optional[str] = None,
    server_base: Optional[str] = None,
    save_snapshot_path: Optional[str] = None,
    auto_delete_orphaned: bool = False,
) -> Dict[str, Any]:
    """
    一键完成：从 ShowDoc 抓取接口树，然后生成 Android 代码。

    Args:
        base_url: ShowDoc 项目 URL
        cookie: 认证 Cookie（可选，如果提供 password 则可不提供）
        password: 项目访问密码（默认: "123456"），如果提供 cookie 则可不提供，将自动进行验证码登录
        node_name: 节点名称（分类），None/"全部"/"all" 表示全量
        base_package: Kotlin 包名
        output_dir: 输出目录（None 使用 android_output）
        server_base: ShowDoc 服务器根地址，用于生成文档链接
        save_snapshot_path: 可选，本地快照保存路径
        auto_delete_orphaned: 是否自动删除已孤立/待删除的旧文件（默认 False：只标记不删除）

    Returns:
        {
            "ok": bool,
            "error": Optional[str],
            "stage": Literal["fetch", "generate", None],
            "snapshot_path": Optional[str],
            "output_dir": Optional[str],
            "generated": Optional[dict],
        }
    """
    # 第一步：抓取 ShowDoc
    fetch_result = showdoc_fetch_apis(
        base_url=base_url,
        cookie=cookie,
        password=password,
        node_name=node_name,
        save_path=save_snapshot_path,
    )
    if not fetch_result.get("ok"):
        return {
            "ok": False,
            "error": fetch_result.get("error") or "fetch_failed",
            "stage": "fetch",
            "snapshot_path": fetch_result.get("snapshot_path"),
            "output_dir": None,
            "generated": None,
        }

    api_tree_json = fetch_result.get("api_tree") or {}

    # server_base 未传时，尽量从 base_url 推断
    if server_base is None:
        server_base = _extract_server_base(base_url) or None

    # 第二步：生成 Android 代码
    gen_result = android_generate_from_showdoc(
        api_tree_json=api_tree_json,
        snapshot_path=None,
        base_package=base_package,
        output_dir=output_dir,
        category_filter=node_name,
        server_base=server_base,
        auto_delete_orphaned=auto_delete_orphaned,
    )

    if not gen_result.get("ok"):
        return {
            "ok": False,
            "error": gen_result.get("error") or "generate_failed",
            "stage": "generate",
            "snapshot_path": fetch_result.get("snapshot_path"),
            "output_dir": None,
            "generated": None,
        }

    return {
        "ok": True,
        "error": None,
        "stage": None,
        "snapshot_path": fetch_result.get("snapshot_path"),
        "output_dir": gen_result.get("output_dir"),
        "generated": gen_result.get("generated"),
    }


__all__.append("showdoc_fetch_and_generate")


# ========== MCP stdio Server（简易实现） ==========

ToolFunc = Callable[..., Dict[str, Any]]


def _build_tool_schemas() -> Dict[str, Dict[str, Any]]:
    """
    为 MCP 的 tools/list 提供简单的 JSON Schema 描述。
    不追求 100% 严格，只要参数名和类型大致正确即可。
    """
    return {
        "showdoc_fetch_apis": {
            "name": "showdoc_fetch_apis",
            "description": "从 ShowDoc 抓取接口树，并可选保存为本地快照。",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "base_url": {"type": "string"},
                    "cookie": {"type": "string"},
                    "node_name": {"type": ["string", "null"]},
                    "save_path": {"type": ["string", "null"]},
                },
                "required": ["base_url", "cookie"],
            },
        },
        "android_generate_from_showdoc": {
            "name": "android_generate_from_showdoc",
            "description": "基于 ShowDoc 抓取结果（JSON 或快照文件）生成 Android 代码。",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "api_tree_json": {"type": ["object", "null"]},
                    "snapshot_path": {"type": ["string", "null"]},
                    "base_package": {"type": "string", "default": "com.example.api"},
                    "output_dir": {"type": ["string", "null"]},
                    "category_filter": {"type": ["string", "null"]},
                    "server_base": {"type": ["string", "null"]},
                },
                "required": [],
            },
        },
        "android_open_output_folder": {
            "name": "android_open_output_folder",
            "description": "返回（可选尝试在本机打开）当前 Android 输出目录。",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "output_dir": {"type": ["string", "null"]},
                    "open_in_explorer": {"type": "boolean", "default": False},
                },
                "required": [],
            },
        },
        "showdoc_fetch_and_generate": {
            "name": "showdoc_fetch_and_generate",
            "description": "一键从 ShowDoc 抓取接口树并生成 Android 代码。",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "base_url": {"type": "string"},
                    "cookie": {"type": "string"},
                    "node_name": {"type": ["string", "null"]},
                    "base_package": {"type": "string", "default": "com.example.api"},
                    "output_dir": {"type": ["string", "null"]},
                    "server_base": {"type": ["string", "null"]},
                    "save_snapshot_path": {"type": ["string", "null"]},
                },
                "required": ["base_url", "cookie"],
            },
        },
    }


def _get_tool_registry() -> Dict[str, ToolFunc]:
    """工具名称到实际函数的映射。"""
    return {
        "showdoc_fetch_apis": showdoc_fetch_apis,
        "android_generate_from_showdoc": android_generate_from_showdoc,
        "android_open_output_folder": android_open_output_folder,
        "showdoc_fetch_and_generate": showdoc_fetch_and_generate,
    }


def _handle_initialize(request: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "jsonrpc": "2.0",
        "id": request.get("id"),
        "result": {
            "serverInfo": {
                "name": "showdoc-android-mcp",
                "version": "0.1.0",
            },
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "tools": {},
            },
        },
    }


def _handle_tools_list(request: Dict[str, Any]) -> Dict[str, Any]:
    tools = list(_build_tool_schemas().values())
    return {
        "jsonrpc": "2.0",
        "id": request.get("id"),
        "result": {
            "tools": tools,
        },
    }


def _handle_tools_call(request: Dict[str, Any]) -> Dict[str, Any]:
    params = request.get("params") or {}
    name = params.get("name")
    arguments = params.get("arguments") or {}

    registry = _get_tool_registry()
    if name not in registry:
        return {
            "jsonrpc": "2.0",
            "id": request.get("id"),
            "error": {
                "code": -32601,
                "message": f"Tool not found: {name}",
            },
        }

    func = registry[name]
    try:
        result = func(**arguments)
    except TypeError as e:
        return {
            "jsonrpc": "2.0",
            "id": request.get("id"),
            "error": {
                "code": -32602,
                "message": f"Invalid params for tool '{name}': {e}",
            },
        }
    except Exception as e:
        return {
            "jsonrpc": "2.0",
            "id": request.get("id"),
            "error": {
                "code": -32000,
                "message": f"Tool '{name}' failed: {e}",
            },
        }

    # 按 MCP 约定，返回 content 数组，其中包含一个 json 类型的结果
    return {
        "jsonrpc": "2.0",
        "id": request.get("id"),
        "result": {
            "content": [
                {
                    "type": "json",
                    "json": result,
                }
            ]
        },
    }


def _dispatch_request(request: Dict[str, Any]) -> Dict[str, Any]:
    method = request.get("method")

    if method == "initialize":
        return _handle_initialize(request)
    if method == "tools/list":
        return _handle_tools_list(request)
    if method == "tools/call":
        return _handle_tools_call(request)

    return {
        "jsonrpc": "2.0",
        "id": request.get("id"),
        "error": {
            "code": -32601,
            "message": f"Method not found: {method}",
        },
    }


def _read_message() -> Optional[Dict[str, Any]]:
    """
    按 MCP/LSP 约定从 stdin 读取一条带 Content-Length 头的 JSON-RPC 消息。
    """
    # 读取 header
    content_length: Optional[int] = None
    while True:
        line = sys.stdin.buffer.readline()
        if not line:
            # EOF
            return None
        decoded = line.decode("utf-8").strip()
        if not decoded:
            # 空行，header 结束
            break
        lower = decoded.lower()
        if lower.startswith("content-length:"):
            try:
                content_length = int(decoded.split(":", 1)[1].strip())
            except ValueError:
                pass
    if content_length is None or content_length <= 0:
        return None

    body = sys.stdin.buffer.read(content_length)
    if not body:
        return None
    try:
        return json.loads(body.decode("utf-8"))
    except json.JSONDecodeError:
        return {
            "jsonrpc": "2.0",
            "id": None,
            "error": {
                "code": -32700,
                "message": "Parse error",
            },
        }


def _write_message(response: Dict[str, Any]) -> None:
    """按 MCP/LSP 约定向 stdout 写入一条带 Content-Length 头的 JSON-RPC 消息。"""
    body = json.dumps(response, ensure_ascii=False).encode("utf-8")
    header = f"Content-Length: {len(body)}\r\n\r\n".encode("ascii")
    sys.stdout.buffer.write(header)
    sys.stdout.buffer.write(body)
    sys.stdout.buffer.flush()


def run_stdio_mcp_server() -> None:
    """
    MCP JSON-RPC stdio 服务器（Content-Length 帧格式）。
    """
    while True:
        request = _read_message()
        if request is None:
            break
        response = _dispatch_request(request)
        _write_message(response)


if __name__ == "__main__":
    # 当以 `python -m mcp_showdoc_android.server` 运行时，
    # 启动一个基于 stdin/stdout 的简易 MCP Server。
    run_stdio_mcp_server()




