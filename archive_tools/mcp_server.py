"""
压缩解压 MCP 工具封装

将压缩解压功能封装为 MCP 工具，供 Cursor 等 MCP 客户端调用。
"""

from __future__ import annotations

import asyncio
from typing import Optional, Annotated, List

try:
    from mcp.server.fastmcp import FastMCP, ToolError
except ImportError:
    from mcp.server.fastmcp import FastMCP

    class ToolError(RuntimeError):
        """Fallback ToolError for旧版本 MCP。"""
        pass

from .server import compress_files, extract_archive


# 创建独立的 FastMCP 应用实例（可选，也可以直接导出函数供主服务器使用）
# 这里我们导出函数，让主服务器注册


async def compress_files_tool(
    source_paths: Annotated[List[str], "要压缩的文件或目录路径列表"],
    output_path: Annotated[str, "输出压缩文件路径"],
    format: Annotated[str, "压缩格式：zip、7z 或 rar（默认 zip）"] = "zip",
    compression_level: Annotated[int, "压缩级别：0-9，0=最快，9=最小（默认 6）"] = 6,
    compression_method: Annotated[str, "压缩方式：standard、store、fastest、best（默认 standard）"] = "standard",
    password: Annotated[Optional[str], "压缩密码（可选）"] = None,
    split_size: Annotated[Optional[str], "分卷大小，如 '100MB'、'1GB'（可选）"] = None,
    delete_source: Annotated[bool, "压缩后删除源文件（默认 False）"] = False,
    store_low_ratio: Annotated[bool, "直接存储压缩率低的文件（默认 False）"] = False,
    separate_archives: Annotated[bool, "压缩每个文件到单独的压缩包（默认 False）"] = False,
) -> dict:
    """
    压缩文件或目录。
    
    支持 ZIP、7Z、RAR 格式的压缩，提供多种压缩选项：
    - 压缩级别：0（最快）到 9（最小）
    - 密码保护
    - 分卷压缩
    - 压缩后删除源文件
    - 每个文件单独压缩
    
    必需参数：
    - source_paths: 要压缩的文件或目录路径列表
    - output_path: 输出压缩文件路径
    
    可选参数：
    - format: 压缩格式（zip、7z、rar），默认 zip
    - compression_level: 压缩级别（0-9），默认 6
    - compression_method: 压缩方式，默认 standard
    - password: 压缩密码
    - split_size: 分卷大小（如 "100MB"、"1GB"）
    - delete_source: 压缩后删除源文件
    - store_low_ratio: 直接存储压缩率低的文件
    - separate_archives: 压缩每个文件到单独的压缩包
    """
    if not source_paths:
        raise ToolError("source_paths 参数不能为空")
    
    if not output_path:
        raise ToolError("output_path 参数不能为空")
    
    # 验证压缩级别
    if compression_level < 0 or compression_level > 9:
        raise ToolError("compression_level 必须在 0-9 之间")
    
    # 验证格式
    format_lower = format.lower()
    if format_lower not in ["zip", "7z", "rar"]:
        raise ToolError("format 必须是 zip、7z 或 rar")
    
    # 在线程中执行压缩（避免阻塞）
    result = await asyncio.to_thread(
        compress_files,
        source_paths=source_paths,
        output_path=output_path,
        format=format_lower,
        compression_level=compression_level,
        compression_method=compression_method,
        password=password,
        split_size=split_size,
        delete_source=delete_source,
        store_low_ratio=store_low_ratio,
        separate_archives=separate_archives,
    )
    
    if not result.get("ok"):
        raise ToolError(result.get("error") or "压缩失败")
    
    return result


async def extract_archive_tool(
    archive_path: Annotated[str, "要解压的压缩文件路径"],
    output_dir: Annotated[Optional[str], "输出目录（可选，默认解压到压缩文件所在目录）"] = None,
    password: Annotated[Optional[str], "解压密码（可选）"] = None,
    delete_archive: Annotated[bool, "解压后删除压缩包（默认 False）"] = False,
) -> dict:
    """
    解压压缩文件。
    
    支持 ZIP、7Z、RAR 格式的解压，自动识别格式。
    
    必需参数：
    - archive_path: 要解压的压缩文件路径
    
    可选参数：
    - output_dir: 输出目录，默认解压到压缩文件所在目录
    - password: 解压密码
    - delete_archive: 解压后删除压缩包
    """
    if not archive_path:
        raise ToolError("archive_path 参数不能为空")
    
    # 在线程中执行解压（避免阻塞）
    result = await asyncio.to_thread(
        extract_archive,
        archive_path=archive_path,
        output_dir=output_dir,
        password=password,
        delete_archive=delete_archive,
    )
    
    if not result.get("ok"):
        raise ToolError(result.get("error") or "解压失败")
    
    return result


__all__ = ["compress_files_tool", "extract_archive_tool"]

