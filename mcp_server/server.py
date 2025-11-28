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
from flutter_codegen import FlutterCodeGenerator


# ========== 通用配置 ==========

DEFAULT_OUTPUT_DIR = "output/android_output"
DEFAULT_FLUTTER_OUTPUT_DIR = "output/flutter_output"
DEFAULT_SNAPSHOT_DIR = "output/showdoc_snapshots"


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


def _normalize_output_dir(output_dir: Optional[str], default_dir: Optional[str] = None) -> Path:
    """
    统一处理输出目录，None 时使用默认目录。
    
    输出目录是相对于当前工作目录（通常是项目根目录）的相对路径。
    如果 output_dir 是相对路径，将相对于当前工作目录解析。
    如果 output_dir 是绝对路径，则直接使用。
    """
    if not output_dir:
        output_dir = default_dir or DEFAULT_OUTPUT_DIR
    
    # 如果是绝对路径，直接使用
    output_path = Path(output_dir)
    if output_path.is_absolute():
        return output_path.resolve()
    
    # 如果是相对路径，相对于当前工作目录（通常是项目根目录）
    return Path.cwd() / output_dir


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


def _generate_auto_snapshot_path(item_id: str, item_name: str = "") -> Path:
    """生成自动快照保存路径。
    
    Args:
        item_id: 项目 ID
        item_name: 项目名称（可选，用于文件名）
    
    Returns:
        快照文件路径
    """
    from datetime import datetime
    
    snapshot_dir = Path(DEFAULT_SNAPSHOT_DIR)
    snapshot_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = "".join(c for c in item_name if c.isalnum() or c in (" ", "-", "_")).strip()[:30]
    if safe_name:
        filename = f"{item_id}_{safe_name}_{timestamp}.json"
    else:
        filename = f"{item_id}_{timestamp}.json"
    
    return snapshot_dir / filename


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
        node_name: 可选节点名称（分类），None/"全部"/"all" 表示全量；如果 base_url 包含页面 ID（如 /94/4828），且 node_name 为空，则自动抓取该页面所在的节点
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
        # 从 base_url 中提取 page_id（如果 URL 包含页面 ID）
        from core.parser import parse_showdoc_url
        url_info = parse_showdoc_url(base_url)
        extracted_page_id = url_info.get("page_id")
        
        # 如果 base_url 包含 page_id 且没有指定 node_name，则使用 page_id 作为节点筛选
        actual_node_name = node_name
        actual_page_id = None
        if extracted_page_id and not node_name:
            actual_page_id = extracted_page_id
        
        client = ShowDocClient(base_url, cookie=cookie, password=password)
        api_tree = client.get_all_apis(node_name=actual_node_name, page_id=actual_page_id)
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
        else:
            # 自动保存到 output/showdoc_snapshots/
            snapshot_file = _generate_auto_snapshot_path(
                api_tree.item_info.item_id,
                api_tree.item_info.item_name
            )
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


def showdoc_fetch_node_tree(
    base_url: str,
    cookie: Optional[str] = None,
    password: Optional[str] = "123456",
    node_name: Optional[str] = None,
) -> Dict[str, Any]:
    """
    仅抓取节点树状结构（不含 API 详情），每个节点包含跳转链接。
    
    Args:
        base_url: ShowDoc 项目 URL，如果包含页面 ID（如 /94/4828），且 node_name 为空，则自动筛选该页面所在的节点
        cookie: 认证 Cookie（可选）
        password: 项目访问密码（可选）
        node_name: 可选节点名称（分类），None/"全部"/"all" 表示全量
    """
    try:
        # 从 base_url 中提取 page_id（如果 URL 包含页面 ID）
        from core.parser import parse_showdoc_url
        url_info = parse_showdoc_url(base_url)
        extracted_page_id = url_info.get("page_id")
        
        # 如果 base_url 包含 page_id 且没有指定 node_name，则使用 page_id 作为节点筛选
        actual_node_name = node_name
        actual_page_id = None
        if extracted_page_id and not node_name:
            actual_page_id = extracted_page_id
        
        client = ShowDocClient(base_url, cookie=cookie, password=password)
        node_tree = client.get_node_tree(node_name=actual_node_name, page_id=actual_page_id)
        return {
            "ok": True,
            "error": None,
            "node_tree": node_tree,
        }
    except ShowDocAuthError as e:
        return {"ok": False, "error": f"auth_error: {e}", "node_tree": None}
    except ShowDocNotFoundError as e:
        return {"ok": False, "error": f"not_found: {e}", "node_tree": None}
    except ShowDocNetworkError as e:
        return {"ok": False, "error": f"network_error: {e}", "node_tree": None}
    except Exception as e:
        return {"ok": False, "error": f"unknown_error: {e}", "node_tree": None}


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
    "showdoc_fetch_node_tree",
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
        node_name: 节点名称（分类），None/"全部"/"all" 表示全量；如果 base_url 包含页面 ID（如 /94/4828），且 node_name 为空，则自动抓取该页面所在的节点
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
    # 第一步：抓取 ShowDoc（如果没有指定保存路径，会自动保存）
    # 注意：showdoc_fetch_apis 内部会自动从 base_url 提取 page_id，如果 node_name 为空则使用 page_id
    fetch_result = showdoc_fetch_apis(
        base_url=base_url,
        cookie=cookie,
        password=password,
        node_name=node_name,  # 如果 base_url 包含页面 ID 且 node_name 为空，会自动使用 page_id
        save_path=save_snapshot_path,  # None 时会自动保存到 output/showdoc_snapshots/
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


# ========== MCP 工具：Flutter 代码生成 ==========

def flutter_generate_from_showdoc(
    api_tree_json: Optional[Dict[str, Any]] = None,
    snapshot_path: Optional[str] = None,
    base_package: str = "com.example.api",
    output_dir: Optional[str] = None,
    category_filter: Optional[str] = None,
    server_base: Optional[str] = None,
    auto_delete_orphaned: bool = False,
) -> Dict[str, Any]:
    """
    基于 ShowDoc 抓取结果生成 Flutter 代码。

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

        out_dir = _normalize_output_dir(output_dir, default_dir=DEFAULT_FLUTTER_OUTPUT_DIR)
        generator = FlutterCodeGenerator(base_package=base_package, output_dir=str(out_dir))

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


def showdoc_fetch_and_generate_flutter(
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
    一键完成：从 ShowDoc 抓取接口树，然后生成 Flutter 代码。

    Args:
        base_url: ShowDoc 项目 URL
        cookie: 认证 Cookie（可选，如果提供 password 则可不提供）
        password: 项目访问密码（默认: "123456"），如果提供 cookie 则可不提供，将自动进行验证码登录
        node_name: 节点名称（分类），None/"全部"/"all" 表示全量；如果 base_url 包含页面 ID（如 /94/4828），且 node_name 为空，则自动抓取该页面所在的节点
        base_package: Dart 包名
        output_dir: 输出目录（None 使用 flutter_output）
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

    # 第二步：生成 Flutter 代码
    gen_result = flutter_generate_from_showdoc(
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


__all__.extend(["flutter_generate_from_showdoc", "showdoc_fetch_and_generate_flutter"])


# ========== MCP 工具 4：查询指定节点详细信息 ==========

def get_node_detail_info(
    base_url: str,
    node_name: Optional[str] = None,
    page_id: Optional[str] = None,
    cookie: Optional[str] = None,
    password: Optional[str] = "123456",
    snapshot_path: Optional[str] = None,
) -> Dict[str, Any]:
    """
    查询指定节点（或URL）的详细信息。
    
    逻辑：
    1. 如果本地有缓存（snapshot_path 或自动查找），优先使用缓存数据
    2. 如果没有缓存，重新抓取数据
    3. 如果节点信息不是API的（api_info为null），调用 /api/page/info 接口获取详细信息
    
    Args:
        base_url: ShowDoc 项目 URL
        node_name: 节点名称（分类名称），可选
        page_id: 页面 ID，可选（如果URL中包含page_id会自动提取）
        cookie: 认证 Cookie，可选
        password: 项目访问密码，默认 "123456"
        snapshot_path: 本地快照文件路径，如果为None则自动查找最新的快照
    
    Returns:
        {
            "ok": bool,
            "error": Optional[str],
            "node_info": Optional[dict],  # 节点详细信息
            "from_cache": bool,  # 是否来自缓存
            "snapshot_path": Optional[str],  # 使用的快照路径
        }
    """
    try:
        from core.parser import parse_showdoc_url
        from pathlib import Path
        import glob
        
        url_info = parse_showdoc_url(base_url)
        item_id = url_info.get("item_id")
        extracted_page_id = url_info.get("page_id")
        
        # 优先使用传入的 page_id，否则使用URL中提取的
        actual_page_id = page_id or extracted_page_id
        
        # 步骤1: 尝试从缓存加载
        api_tree_dict = None
        from_cache = False
        used_snapshot_path = None
        
        if snapshot_path:
            # 使用指定的快照文件
            snapshot_file = Path(snapshot_path).resolve()
            if snapshot_file.exists():
                content = snapshot_file.read_text(encoding="utf-8")
                api_tree_dict = json.loads(content)
                from_cache = True
                used_snapshot_path = str(snapshot_file)
        else:
            # 自动查找最新的快照文件（基于item_id匹配）
            snapshot_dir = Path(DEFAULT_SNAPSHOT_DIR)
            if snapshot_dir.exists():
                # 查找包含该item_id的快照文件
                pattern = str(snapshot_dir / f"*{item_id}*.json")
                snapshot_files = glob.glob(pattern)
                if snapshot_files:
                    # 按修改时间排序，取最新的
                    snapshot_files.sort(key=lambda f: Path(f).stat().st_mtime, reverse=True)
                    latest_snapshot = snapshot_files[0]
                    content = Path(latest_snapshot).read_text(encoding="utf-8")
                    api_tree_dict = json.loads(content)
                    from_cache = True
                    used_snapshot_path = latest_snapshot
        
        # 步骤2: 如果没有缓存，重新抓取
        if not api_tree_dict:
            fetch_result = showdoc_fetch_apis(
                base_url=base_url,
                cookie=cookie,
                password=password,
                node_name=node_name,
                save_path=None,  # 自动保存
            )
            if not fetch_result.get("ok"):
                return {
                    "ok": False,
                    "error": fetch_result.get("error") or "抓取失败",
                    "node_info": None,
                    "from_cache": False,
                    "snapshot_path": None,
                }
            api_tree_dict = fetch_result.get("api_tree")
            used_snapshot_path = fetch_result.get("snapshot_path")
        
        # 步骤3: 从api_tree_dict中提取指定节点信息
        categories = api_tree_dict.get("categories", [])
        
        def find_node_recursive(cat_list: List[Dict[str, Any]], target_name: Optional[str], target_page_id: Optional[str]) -> Optional[Dict[str, Any]]:
            """递归查找节点"""
            for cat in cat_list:
                # 如果指定了page_id，检查当前分类的页面
                if target_page_id:
                    for page in cat.get("pages", []):
                        if str(page.get("page_id", "")) == str(target_page_id):
                            return cat
                
                # 如果指定了node_name，检查分类名称
                if target_name and cat.get("cat_name") == target_name:
                    return cat
                
                # 递归搜索子分类
                children = cat.get("children", [])
                if children:
                    result = find_node_recursive(children, target_name, target_page_id)
                    if result:
                        return result
            return None
        
        # 如果node_name和page_id都为空，返回错误
        if not node_name and not actual_page_id:
            return {
                "ok": False,
                "error": "必须提供 node_name 或 page_id 之一来指定节点",
                "node_info": None,
                "from_cache": from_cache,
                "snapshot_path": used_snapshot_path,
            }
        
        target_node = find_node_recursive(categories, node_name, actual_page_id)
        
        if not target_node:
            return {
                "ok": False,
                "error": f"未找到指定的节点（node_name={node_name}, page_id={actual_page_id}）",
                "node_info": None,
                "from_cache": from_cache,
                "snapshot_path": used_snapshot_path,
            }
        
        # 步骤4: 检查节点中的页面是否有api_info为null的，如果有则调用接口获取详细信息
        server_base = url_info.get("server_base")
        client = None
        
        # 检查是否需要获取cookie
        if not cookie:
            from core.cookie_manager import CookieManager
            cookie_manager = CookieManager()
            cookie = cookie_manager.get_cookie(server_base, item_id)
        
        # 如果有null的api_info，需要调用接口获取
        pages_with_details = []
        for page in target_node.get("pages", []):
            page_info = page.copy()
            
            # 如果api_info为null，调用接口获取详细信息
            if not page.get("api_info") and page.get("page_id"):
                try:
                    if not client:
                        client = ShowDocClient(base_url, cookie=cookie, password=password)
                    
                    page_id_str = str(page.get("page_id"))
                    print(f"[DEBUG] 调用详情接口获取页面 {page_id_str} 的详细信息...")
                    page_data = client.fetch_page_info(page_id_str)
                    
                    api_info = client._parse_api_definition(page_data)
                    
                    if api_info:
                        print(f"[DEBUG] 页面 {page_id_str} 是 API 接口")
                        page_info["api_info"] = {
                            "method": api_info.method,
                            "url": api_info.url,
                            "title": api_info.title,
                            "description": api_info.description,
                            "request": api_info.request,
                            "response": api_info.response,
                        }
                    else:
                        # 即使不是API，也保存页面内容
                        decoded_content = page_data.get("decoded_content")
                        if decoded_content:
                            print(f"[DEBUG] 页面 {page_id_str} 是普通页面，已保存内容")
                            page_info["page_content"] = decoded_content
                        else:
                            print(f"[DEBUG] 页面 {page_id_str} 没有 decoded_content，原始数据: {list(page_data.keys())}")
                except Exception as e:
                    # 获取失败时保留原始信息，但输出更详细的错误
                    import traceback
                    print(f"警告: 获取页面 {page.get('page_id')} 详细信息失败: {e}")
                    print(f"  错误类型: {type(e).__name__}")
                    traceback.print_exc()
            
            pages_with_details.append(page_info)
        
        # 更新节点信息
        target_node["pages"] = pages_with_details
        
        return {
            "ok": True,
            "error": None,
            "node_info": target_node,
            "from_cache": from_cache,
            "snapshot_path": used_snapshot_path,
        }
        
    except Exception as e:
        return {
            "ok": False,
            "error": f"unknown_error: {e}",
            "node_info": None,
            "from_cache": False,
            "snapshot_path": None,
        }


# ========== MCP 工具 5：查询指定节点的Cookie信息 ==========

def get_node_cookie(
    base_url: str,
    cookie: Optional[str] = None,
    password: Optional[str] = "123456",
) -> Dict[str, Any]:
    """
    查询指定节点所需的已登录的cookie信息。
    
    逻辑：
    1. 优先从本地缓存文件（output/.showdoc_cookies.json）读取
    2. 如果没有缓存或已过期，重新走登录逻辑生成并获取
    
    Args:
        base_url: ShowDoc 项目 URL
        cookie: 认证 Cookie，可选（如果提供则直接使用并保存）
        password: 项目访问密码，默认 "123456"
    
    Returns:
        {
            "ok": bool,
            "error": Optional[str],
            "cookie": Optional[str],  # Cookie字符串
            "server_base": Optional[str],  # 服务器地址
            "item_id": Optional[str],  # 项目ID
            "from_cache": bool,  # 是否来自缓存
        }
    """
    try:
        from core.parser import parse_showdoc_url
        from core.cookie_manager import CookieManager
        
        url_info = parse_showdoc_url(base_url)
        server_base = url_info.get("server_base")
        item_id = url_info.get("item_id")
        
        cookie_manager = CookieManager()
        
        # 步骤1: 如果提供了cookie，直接使用并保存
        if cookie:
            cookie_manager.save_cookie(server_base, item_id, cookie)
            return {
                "ok": True,
                "error": None,
                "cookie": cookie,
                "server_base": server_base,
                "item_id": item_id,
                "from_cache": False,
            }
        
        # 步骤2: 尝试从缓存读取
        saved_cookie = cookie_manager.get_cookie(server_base, item_id)
        if saved_cookie:
            return {
                "ok": True,
                "error": None,
                "cookie": saved_cookie,
                "server_base": server_base,
                "item_id": item_id,
                "from_cache": True,
            }
        
        # 步骤3: 如果没有缓存，使用密码登录
        if not password:
            return {
                "ok": False,
                "error": "未找到缓存的Cookie，且未提供password，无法自动登录",
                "cookie": None,
                "server_base": server_base,
                "item_id": item_id,
                "from_cache": False,
            }
        
        # 创建客户端并登录
        client = ShowDocClient(base_url, cookie=None, password=password)
        # 登录成功后，cookie已经保存在client中
        final_cookie = client.cookie
        
        if not final_cookie:
            return {
                "ok": False,
                "error": "登录失败，无法获取Cookie",
                "cookie": None,
                "server_base": server_base,
                "item_id": item_id,
                "from_cache": False,
            }
        
        return {
            "ok": True,
            "error": None,
            "cookie": final_cookie,
            "server_base": server_base,
            "item_id": item_id,
            "from_cache": False,
        }
        
    except ShowDocAuthError as e:
        return {
            "ok": False,
            "error": f"auth_error: {e}",
            "cookie": None,
            "server_base": None,
            "item_id": None,
            "from_cache": False,
        }
    except Exception as e:
        return {
            "ok": False,
            "error": f"unknown_error: {e}",
            "cookie": None,
            "server_base": None,
            "item_id": None,
            "from_cache": False,
        }


__all__.extend(["get_node_detail_info", "get_node_cookie"])


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
                    "base_url": {"type": "string", "description": "ShowDoc 项目 URL（支持 web/#/、password、share 链接）"},
                    "cookie": {"type": "string", "description": "可选，浏览器复制的 Cookie，用于免验证码登录"},
                    "password": {"type": ["string", "null"], "description": "可选，项目访问密码（留空则仅靠 Cookie）"},
                    "node_name": {"type": ["string", "null"], "description": "可选，只抓取指定节点；None/全部/all 表示全量"},
                    "save_path": {"type": ["string", "null"], "description": "可选，本地快照保存路径（.json）"},
                },
                "required": ["base_url"],
            },
        },
        "showdoc_fetch_node_tree": {
            "name": "showdoc_fetch_node_tree",
            "description": "仅抓取 ShowDoc 节点树状结构（不含 API 详情）。",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "base_url": {"type": "string", "description": "ShowDoc 项目 URL（支持分享链接）"},
                    "cookie": {"type": "string", "description": "可选，已有 Cookie，用于跳过验证码"},
                    "password": {"type": ["string", "null"], "description": "可选，项目访问密码（默认 123456）"},
                    "node_name": {"type": ["string", "null"], "description": "可选，只返回某个节点的子树"},
                },
                "required": ["base_url"],
            },
        },
        "android_generate_from_showdoc": {
            "name": "android_generate_from_showdoc",
            "description": "基于 ShowDoc 抓取结果（JSON 或快照文件）生成 Android 代码。",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "api_tree_json": {"type": ["object", "null"], "description": "来自 showdoc_fetch_apis 的原始 JSON"},
                    "snapshot_path": {"type": ["string", "null"], "description": "本地快照文件路径（api_tree_json 为空时使用）"},
                    "base_package": {"type": "string", "default": "com.example.api", "description": "生成代码的 Kotlin 包名"},
                    "output_dir": {"type": ["string", "null"], "description": "输出目录，默认 android_output"},
                    "category_filter": {"type": ["string", "null"], "description": "可选，仅生成某个分类"},
                    "server_base": {"type": ["string", "null"], "description": "文档链接前缀，留空则自动推断"},
                    "auto_delete_orphaned": {"type": "boolean", "default": False, "description": "是否自动删除已失效文件"},
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
                    "output_dir": {"type": ["string", "null"], "description": "指定输出目录，默认 android_output"},
                    "open_in_explorer": {"type": "boolean", "default": False, "description": "是否尝试用系统文件管理器打开"},
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
                    "base_url": {"type": "string", "description": "ShowDoc 项目 URL"},
                    "cookie": {"type": "string", "description": "可选，浏览器 Cookie"},
                    "password": {"type": ["string", "null"], "description": "可选，项目访问密码"},
                    "node_name": {"type": ["string", "null"], "description": "可选，只生成某个节点"},
                    "base_package": {"type": "string", "default": "com.example.api", "description": "生成代码的 Kotlin 包名"},
                    "output_dir": {"type": ["string", "null"], "description": "输出目录"},
                    "server_base": {"type": ["string", "null"], "description": "文档链接前缀"},
                    "save_snapshot_path": {"type": ["string", "null"], "description": "可选，抓取结果保存路径"},
                    "auto_delete_orphaned": {"type": "boolean", "default": False, "description": "是否自动删除无用文件"},
                },
                "required": ["base_url"],
            },
        },
    }


def _get_tool_registry() -> Dict[str, ToolFunc]:
    """工具名称到实际函数的映射。"""
    return {
        "showdoc_fetch_apis": showdoc_fetch_apis,
        "showdoc_fetch_node_tree": showdoc_fetch_node_tree,
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
                "name": "showdoc-mcp",
                "version": "1.0.0",
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
    # 当以 `python -m mcp_showdoc.server` 运行时，
    # 启动一个基于 stdin/stdout 的简易 MCP Server。
    run_stdio_mcp_server()




