"""
File Operations MCP 工具封装

将文件操作功能封装为 MCP 工具，供 Cursor 等 MCP 客户端调用。
"""

from __future__ import annotations

import asyncio
from typing import Optional, Annotated, List, Dict, Any

try:
    from mcp.server.fastmcp import FastMCP, ToolError
except ImportError:
    from mcp.server.fastmcp import FastMCP

    class ToolError(RuntimeError):
        """Fallback ToolError for旧版本 MCP。"""
        pass

from .file_utils import (
    copy_file,
    move_file,
    delete_file,
    create_file,
    create_directory,
    rename_file,
    file_exists,
    get_file_info,
)
from .content_processor import (
    read_file_safe,
    write_file_safe,
    replace_content,
    merge_files,
)
from .batch_operations import (
    batch_copy,
    batch_move,
    batch_delete,
    batch_rename,
    batch_replace_content,
)
from .file_search import (
    find_files,
    search_content,
    filter_files,
)
from .code_operations import (
    insert_code_block,
    replace_code_block,
    delete_code_block,
    extract_code_block,
    find_code_block,
)
from .template_engine import (
    generate_from_template,
    generate_batch_from_template,
)
from .project_analyzer import (
    generate_file_tree,
    analyze_project,
)
from .file_comparison import (
    compare_files,
    compare_directories,
    get_file_hash,
)
from .content_analyzer import (
    count_lines,
    analyze_file_size,
    search_text,
)
from .git_integration import (
    is_file_tracked,
    get_file_git_status,
    is_file_ignored,
    add_file_to_git,
    batch_add_to_git,
)
from .format_handlers import (
    read_json,
    write_json,
    read_yaml,
    write_yaml,
)
from .backup_manager import (
    backup_file,
    restore_file,
    list_backups,
)


# ========== 基础文件操作工具 ==========

async def mcp_file_create(
    file_path: Annotated[str, "要创建的文件路径"],
    content: Annotated[str, "文件内容（默认空字符串）"] = "",
    encoding: Annotated[str, "文件编码（默认 utf-8）"] = "utf-8",
) -> dict:
    """创建一个新文件。"""
    try:
        result = await asyncio.to_thread(create_file, file_path, content, encoding)
        return {"ok": True, "file_path": str(result)}
    except Exception as e:
        raise ToolError(f"创建文件失败: {e}")


async def mcp_file_read(
    file_path: Annotated[str, "要读取的文件路径"],
    encoding: Annotated[Optional[str], "文件编码（默认自动检测）"] = None,
) -> dict:
    """读取一个文件的内容。"""
    try:
        result = await asyncio.to_thread(read_file_safe, file_path, encoding)
        return {"ok": True, "content": result}
    except Exception as e:
        raise ToolError(f"读取文件失败: {e}")


async def mcp_file_update(
    file_path: Annotated[str, "要更新的文件路径"],
    content: Annotated[str, "新的文件内容"],
    encoding: Annotated[str, "文件编码（默认 utf-8）"] = "utf-8",
    append: Annotated[bool, "是否追加内容（默认 False，即覆盖）"] = False,
) -> dict:
    """更新一个文件的内容。"""
    try:
        if append:
            from .content_processor import append_to_file
            result = await asyncio.to_thread(append_to_file, file_path, content, encoding)
        else:
            result = await asyncio.to_thread(write_file_safe, file_path, content, encoding)
        return {"ok": True, "file_path": str(result)}
    except Exception as e:
        raise ToolError(f"更新文件失败: {e}")


async def mcp_file_delete(
    file_path: Annotated[str, "要删除的文件或目录路径"],
    recursive: Annotated[bool, "如果是目录，是否递归删除（默认 False）"] = False,
) -> dict:
    """删除一个文件或目录。"""
    try:
        from pathlib import Path
        path = Path(file_path)
        
        if path.is_dir() and recursive:
            import shutil
            await asyncio.to_thread(shutil.rmtree, path)
        else:
            await asyncio.to_thread(delete_file, file_path)
        return {"ok": True}
    except Exception as e:
        raise ToolError(f"删除文件失败: {e}")


async def mcp_file_copy(
    source_path: Annotated[str, "源文件或目录路径"],
    destination_path: Annotated[str, "目标文件或目录路径"],
    overwrite: Annotated[bool, "如果目标文件已存在是否覆盖（默认 False）"] = False,
) -> dict:
    """复制一个文件或目录。"""
    try:
        from pathlib import Path
        source = Path(source_path)
        dest = Path(destination_path)
        
        if source.is_dir():
            import shutil
            await asyncio.to_thread(shutil.copytree, source, dest, dirs_exist_ok=overwrite)
        else:
            await asyncio.to_thread(copy_file, source, dest, overwrite)
        return {"ok": True, "destination": str(dest)}
    except Exception as e:
        raise ToolError(f"复制文件失败: {e}")


async def mcp_file_move(
    source_path: Annotated[str, "源文件或目录路径"],
    destination_path: Annotated[str, "目标文件或目录路径"],
    overwrite: Annotated[bool, "如果目标文件已存在是否覆盖（默认 False）"] = False,
) -> dict:
    """移动或重命名一个文件或目录。"""
    try:
        from pathlib import Path
        source = Path(source_path)
        dest = Path(destination_path)
        
        if source.is_dir():
            import shutil
            if dest.exists() and overwrite:
                await asyncio.to_thread(shutil.rmtree, dest)
            await asyncio.to_thread(shutil.move, source, dest)
        else:
            await asyncio.to_thread(move_file, source, dest, overwrite)
        return {"ok": True, "destination": str(dest)}
    except Exception as e:
        raise ToolError(f"移动文件失败: {e}")


async def mcp_file_rename(
    file_path: Annotated[str, "要重命名的文件或目录路径"],
    new_name: Annotated[str, "新的名称"],
) -> dict:
    """重命名一个文件或目录。"""
    try:
        result = await asyncio.to_thread(rename_file, file_path, new_name)
        return {"ok": True, "new_path": str(result)}
    except Exception as e:
        raise ToolError(f"重命名文件失败: {e}")


async def mcp_file_get_info(
    file_path: Annotated[str, "要获取信息的文件路径"],
) -> dict:
    """获取文件或目录的信息。"""
    try:
        result = await asyncio.to_thread(get_file_info, file_path)
        return {"ok": True, "info": result}
    except Exception as e:
        raise ToolError(f"获取文件信息失败: {e}")


# ========== 批量操作工具 ==========

async def mcp_file_create_batch(
    files: Annotated[List[Dict[str, str]], "要创建的文件列表，每个元素是包含 file_path 和 content 的字典"],
) -> dict:
    """批量创建多个文件。"""
    try:
        results = {"success": [], "failed": []}
        for file_info in files:
            try:
                file_path = file_info.get("file_path")
                content = file_info.get("content", "")
                encoding = file_info.get("encoding", "utf-8")
                result = await asyncio.to_thread(create_file, file_path, content, encoding)
                results["success"].append({"file_path": str(result)})
            except Exception as e:
                results["failed"].append({"file_path": file_info.get("file_path"), "error": str(e)})
        return {"ok": True, "results": results}
    except Exception as e:
        raise ToolError(f"批量创建文件失败: {e}")


async def mcp_file_read_batch(
    file_paths: Annotated[List[str], "要读取的文件路径列表"],
    encoding: Annotated[Optional[str], "文件编码（默认自动检测）"] = None,
) -> dict:
    """批量读取多个文件的内容。"""
    try:
        results = {"success": [], "failed": []}
        for file_path in file_paths:
            try:
                content = await asyncio.to_thread(read_file_safe, file_path, encoding)
                results["success"].append({"file_path": file_path, "content": content})
            except Exception as e:
                results["failed"].append({"file_path": file_path, "error": str(e)})
        return {"ok": True, "results": results}
    except Exception as e:
        raise ToolError(f"批量读取文件失败: {e}")


async def mcp_file_update_batch(
    files: Annotated[List[Dict[str, Any]], "要更新的文件列表，每个元素是包含 file_path、content 和 mode 的字典"],
) -> dict:
    """批量更新多个文件的内容。"""
    try:
        results = {"success": [], "failed": []}
        for file_info in files:
            try:
                file_path = file_info.get("file_path")
                content = file_info.get("content", "")
                encoding = file_info.get("encoding", "utf-8")
                append = file_info.get("append", False)
                if append:
                    from .content_processor import append_to_file
                    result = await asyncio.to_thread(append_to_file, file_path, content, encoding)
                else:
                    result = await asyncio.to_thread(write_file_safe, file_path, content, encoding)
                results["success"].append({"file_path": str(result)})
            except Exception as e:
                results["failed"].append({"file_path": file_info.get("file_path"), "error": str(e)})
        return {"ok": True, "results": results}
    except Exception as e:
        raise ToolError(f"批量更新文件失败: {e}")


async def mcp_file_delete_batch(
    file_paths: Annotated[List[str], "要删除的文件或目录路径列表"],
    recursive: Annotated[bool, "如果是目录，是否递归删除（默认 False）"] = False,
) -> dict:
    """批量删除多个文件或目录。"""
    try:
        results = {"success": [], "failed": []}
        for file_path in file_paths:
            try:
                from pathlib import Path
                path = Path(file_path)
                if path.is_dir() and recursive:
                    import shutil
                    await asyncio.to_thread(shutil.rmtree, path)
                else:
                    await asyncio.to_thread(delete_file, file_path)
                results["success"].append({"file_path": file_path})
            except Exception as e:
                results["failed"].append({"file_path": file_path, "error": str(e)})
        return {"ok": True, "results": results}
    except Exception as e:
        raise ToolError(f"批量删除文件失败: {e}")


# ========== 目录操作工具 ==========

async def mcp_file_list_directory(
    directory_path: Annotated[str, "要列出内容的目录路径"],
    recursive: Annotated[bool, "是否递归列出子目录内容（默认 False）"] = False,
    show_hidden: Annotated[bool, "是否显示隐藏文件（默认 False）"] = False,
) -> dict:
    """列出目录中的文件和子目录。"""
    try:
        from pathlib import Path
        dir_path = Path(directory_path)
        
        if not dir_path.exists() or not dir_path.is_dir():
            raise ToolError(f"目录不存在: {directory_path}")
        
        items = []
        if recursive:
            paths = dir_path.rglob("*")
        else:
            paths = dir_path.iterdir()
        
        for path in paths:
            if not show_hidden and path.name.startswith("."):
                continue
            items.append({
                "name": path.name,
                "path": str(path),
                "is_file": path.is_file(),
                "is_dir": path.is_dir(),
            })
        
        return {"ok": True, "items": items}
    except Exception as e:
        raise ToolError(f"列出目录内容失败: {e}")


async def mcp_file_create_directory(
    directory_path: Annotated[str, "要创建的目录路径"],
    recursive: Annotated[bool, "是否递归创建父目录（默认 False）"] = False,
) -> dict:
    """创建一个新目录。"""
    try:
        result = await asyncio.to_thread(create_directory, directory_path, parents=recursive)
        return {"ok": True, "directory_path": str(result)}
    except Exception as e:
        raise ToolError(f"创建目录失败: {e}")


async def mcp_file_search_files(
    directory_path: Annotated[str, "要搜索的目录路径"],
    pattern: Annotated[str, "文件名称匹配模式"],
    recursive: Annotated[bool, "是否递归搜索子目录（默认 False）"] = False,
) -> dict:
    """在目录中搜索匹配指定模式的文件。"""
    try:
        results = await asyncio.to_thread(find_files, directory_path, pattern=pattern, recursive=recursive)
        return {"ok": True, "files": [str(f) for f in results]}
    except Exception as e:
        raise ToolError(f"搜索文件失败: {e}")


async def mcp_file_get_info_batch(
    file_paths: Annotated[List[str], "要获取信息的文件路径列表"],
) -> dict:
    """批量获取多个文件或目录的信息。"""
    try:
        results = {"success": [], "failed": []}
        for file_path in file_paths:
            try:
                info = await asyncio.to_thread(get_file_info, file_path)
                results["success"].append({"file_path": file_path, "info": info})
            except Exception as e:
                results["failed"].append({"file_path": file_path, "error": str(e)})
        return {"ok": True, "results": results}
    except Exception as e:
        raise ToolError(f"批量获取文件信息失败: {e}")


# ========== 高级功能工具 ==========

async def mcp_file_search_content(
    directory_path: Annotated[str, "要搜索的目录路径"],
    search_text: Annotated[str, "要搜索的文本"],
    pattern: Annotated[Optional[str], "文件名模式（只搜索匹配的文件）"] = None,
    regex: Annotated[bool, "是否使用正则表达式（默认 False）"] = False,
) -> dict:
    """搜索文件内容。"""
    try:
        results = await asyncio.to_thread(
            search_content,
            directory_path,
            search_text,
            pattern=pattern,
            regex=regex,
        )
        return {"ok": True, "results": results}
    except Exception as e:
        raise ToolError(f"搜索文件内容失败: {e}")


async def mcp_file_replace_content(
    file_path: Annotated[str, "文件路径"],
    old_text: Annotated[str, "要替换的文本"],
    new_text: Annotated[str, "替换后的文本"],
    regex: Annotated[bool, "是否使用正则表达式（默认 False）"] = False,
) -> dict:
    """替换文件内容。"""
    try:
        count = await asyncio.to_thread(replace_content, file_path, old_text, new_text, regex=regex)
        return {"ok": True, "replacements": count}
    except Exception as e:
        raise ToolError(f"替换文件内容失败: {e}")


async def mcp_file_compare(
    file1_path: Annotated[str, "第一个文件路径"],
    file2_path: Annotated[str, "第二个文件路径"],
) -> dict:
    """比较两个文件。"""
    try:
        result = await asyncio.to_thread(compare_files, file1_path, file2_path)
        return {"ok": True, "comparison": result}
    except Exception as e:
        raise ToolError(f"比较文件失败: {e}")


async def mcp_file_analyze_project(
    root_dir: Annotated[str, "项目根目录"],
) -> dict:
    """分析项目结构。"""
    try:
        result = await asyncio.to_thread(analyze_project, root_dir)
        return {"ok": True, "analysis": result}
    except Exception as e:
        raise ToolError(f"分析项目失败: {e}")


async def mcp_file_generate_from_template(
    template_path: Annotated[str, "模板文件路径"],
    output_path: Annotated[str, "输出文件路径"],
    variables: Annotated[Optional[Dict[str, Any]], "模板变量字典"] = None,
) -> dict:
    """从模板生成文件。"""
    try:
        result = await asyncio.to_thread(
            generate_from_template,
            template_path,
            output_path,
            variables=variables or {},
        )
        return {"ok": True, "output_path": str(result)}
    except Exception as e:
        raise ToolError(f"从模板生成文件失败: {e}")


async def mcp_file_git_status(
    file_path: Annotated[str, "文件路径"],
) -> dict:
    """获取文件的 Git 状态。"""
    try:
        status = await asyncio.to_thread(get_file_git_status, file_path)
        tracked = await asyncio.to_thread(is_file_tracked, file_path)
        ignored = await asyncio.to_thread(is_file_ignored, file_path)
        return {
            "ok": True,
            "status": status,
            "tracked": tracked,
            "ignored": ignored,
        }
    except Exception as e:
        raise ToolError(f"获取 Git 状态失败: {e}")


async def mcp_file_backup(
    file_path: Annotated[str, "要备份的文件路径"],
    backup_dir: Annotated[Optional[str], "备份目录（默认在原文件同目录）"] = None,
) -> dict:
    """备份文件。"""
    try:
        result = await asyncio.to_thread(backup_file, file_path, backup_dir=backup_dir)
        return {"ok": True, "backup_path": str(result)}
    except Exception as e:
        raise ToolError(f"备份文件失败: {e}")

